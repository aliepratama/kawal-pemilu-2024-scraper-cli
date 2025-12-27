"""Border processing implementations."""

import cv2
import numpy as np
from typing import Tuple


# ==========================================
# COMMON HELPER FUNCTIONS
# ==========================================
def order_points(pts):
    """Order points in clockwise order starting from top-left."""
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def four_point_transform(image, pts):
    """Apply perspective transform to image."""
    rect = order_points(pts)
    (tl, tr, br, bl) = rect
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    dst = np.array([[0, 0], [maxWidth - 1, 0], [maxWidth - 1, maxHeight - 1], [0, maxHeight - 1]], dtype="float32")
    M = cv2.getPerspectiveTransform(rect, dst)
    return cv2.warpPerspective(image, M, (maxWidth, maxHeight))


def clean_border_fallback(img):
    """Fallback method to remove border."""
    if img is None:
        return img
    h, w = img.shape[:2]
    py, px = int(h*0.15), int(w*0.15)
    return cv2.resize(img[py:h-py, px:w-px], (w, h))


# ==========================================
# WITH BORDER PROCESSOR
# ==========================================
def inset_box_pixels(box, pixels_x=6, pixels_y=6):
    """
    Inset (shrink) box by N pixels from all sides.
    """
    rect = order_points(box)
    (tl, tr, br, bl) = rect
    
    center = np.mean(rect, axis=0)
    new_rect = np.zeros_like(rect)
    
    for i, corner in enumerate(rect):
        vector = center - corner
        length = np.linalg.norm(vector)
        if length == 0:
            continue
        
        move_vector = vector / length * (pixels_x * 1.414)
        new_rect[i] = corner + move_vector
    
    return new_rect


class WithBorderProcessor:
    """Border processor for digits with thick borders."""
    
    def __init__(self, peel_pixels: int = 6):
        """
        Initialize processor.
        
        Args:
            peel_pixels: Number of pixels to peel from border
        """
        self.peel_pixels = peel_pixels
    
    def process(self, img: np.ndarray) -> np.ndarray:
        """
        Process digit with border - peel outer shell.
        
        Strategy: Find outer contour (border), inset it to remove border.
        """
        if img is None or img.size == 0:
            return img
        
        # Padding to isolate border
        pad = 5
        img_padded = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0))
        
        # Inverse threshold (border becomes white)
        gray = cv2.cvtColor(img_padded, cv2.COLOR_BGR2GRAY)
        _, thresh_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find external contours
        contours, _ = cv2.findContours(thresh_inv, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return clean_border_fallback(img)
        
        # Get largest contour (outer shell)
        target_cnt = max(contours, key=cv2.contourArea)
        
        # Validate area
        total_area = img_padded.shape[0] * img_padded.shape[1]
        if cv2.contourArea(target_cnt) < total_area * 0.3:
            return clean_border_fallback(img)
        
        # Get bounding box
        rect = cv2.minAreaRect(target_cnt)
        box = cv2.boxPoints(rect)
        box = np.int32(box)
        
        # Peel the border (inset)
        peeled_box = inset_box_pixels(box, pixels_x=self.peel_pixels, pixels_y=self.peel_pixels)
        peeled_box = np.int32(peeled_box)
        
        # Warp
        warped = four_point_transform(img_padded, peeled_box)
        
        return warped


# ==========================================
# WITHOUT BORDER PROCESSOR
# ==========================================
class WithoutBorderProcessor:
    """Border processor for digits without borders or thin borders."""
    
    def __init__(self, peel_pixels: int = 7):
        """
        Initialize processor.
        
        Args:
            peel_pixels: Number of pixels to peel from border
        """
        self.peel_pixels = peel_pixels
    
    def process(self, img: np.ndarray) -> np.ndarray:
        """
        Process digit without border - direct peel approach.
        
        Strategy: White padding, detect monster (border+digit), shrink box.
        """
        if img is None or img.size == 0:
            return img
        
        # White padding to isolate black border
        pad = 10
        img_padded = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        
        # Inverse threshold
        gray = cv2.cvtColor(img_padded, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find external contour
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return clean_border_fallback(img)
        
        # Get largest contour
        target_cnt = max(contours, key=cv2.contourArea)
        
        # Fit rotated rect
        rect = cv2.minAreaRect(target_cnt)
        (center, (w, h), angle) = rect
        
        # Peel action - shrink box
        new_w = w - (2 * self.peel_pixels)
        new_h = h - (2 * self.peel_pixels)
        
        # Safety check
        if new_w < 10 or new_h < 10:
            return clean_border_fallback(img)
        
        # Update rect with new size
        new_rect = (center, (new_w, new_h), angle)
        box = cv2.boxPoints(new_rect)
        box = np.int32(box)
        
        # Warp
        warped = four_point_transform(img_padded, box)
        
        return warped


def warp_from_mask_initial(image, mask_points):
    """Initial warp from YOLO mask."""
    contour = np.array(mask_points, dtype=np.int32)
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    box = np.int32(box)
    return four_point_transform(image, box)
