import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Optional, Tuple, Dict
import time
import os


# ==========================================
# HELPER FUNCTIONS - COMMON
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


def warp_from_mask_initial(image, mask_points):
    """Initial warp from YOLO mask."""
    contour = np.array(mask_points, dtype=np.int32)
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect)
    box = np.int32(box)
    return four_point_transform(image, box)


def clean_border_fallback(img):
    """Fallback method to remove border."""
    if img is None:
        return img
    h, w = img.shape[:2]
    py, px = int(h*0.15), int(w*0.15)
    return cv2.resize(img[py:h-py, px:w-px], (w, h))


# ==========================================
# WITH BORDER MODE - Inset Box Method
# ==========================================
def inset_box_pixels(box, pixels_x=6, pixels_y=6):
    """
    Inset (shrink) box by N pixels from all sides.
    Used for 'with border' mode to peel away the border.
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


def process_digit_with_border(img):
    """
    Process digit with border - peel outer shell.
    Strategy: Find outer contour (border), inset it to remove border.
    """
    if img is None or img.size == 0:
        return img
    
    # Padding to isolate border
    pad = 5
    img_padded = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0,0,0))
    
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
    peeled_box = inset_box_pixels(box, pixels_x=6, pixels_y=6)
    peeled_box = np.int32(peeled_box)
    
    # Warp
    warped = four_point_transform(img_padded, peeled_box)
    
    return warped


# ==========================================
# WITHOUT BORDER MODE - Direct Peel
# ==========================================
def process_digit_without_border(img, peel_pixels=7):
    """
    Process digit without border - direct peel approach.
    Strategy: White padding, detect monster (border+digit), shrink box.
    """
    if img is None or img.size == 0:
        return img
    
    # White padding to isolate black border
    pad = 10
    img_padded = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(255,255,255))
    
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
    new_w = w - (2 * peel_pixels)
    new_h = h - (2 * peel_pixels)
    
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


# ==========================================
# MAIN DIGIT CROPPER CLASS
# ==========================================
class DigitCropper:
    """
    Main class for cropping vote number digits using YOLOv11-seg.
    """
    
    def __init__(self, model_path: str, border_mode: str = "with_border"):
        """
        Initialize DigitCropper.
        
        Args:
            model_path: Path to YOLO model weights
            border_mode: "with_border" or "without_border"
        """
        self.model = YOLO(model_path)
        self.border_mode = border_mode
    
    def process_image(self, image_path: str) -> Tuple[bool, float, List[np.ndarray]]:
        """
        Process single ROI image and extract all 9 digits.
        
        Args:
            image_path: Path to ROI image
            
        Returns:
            Tuple of (success, inference_time, list of cropped digit images)
        """
        try:
            # Load image
            img_bgr = cv2.imread(image_path)
            if img_bgr is None:
                return False, 0.0, []
            
            # YOLO inference
            start_time = time.time()
            results = self.model.predict(image_path, conf=0.25, iou=0.5, imgsz=1280, verbose=False)
            inference_time = time.time() - start_time
            
            result = results[0]
            
            if result.masks is None:
                return False, inference_time, []
            
            # Extract digits
            digits = self.extract_digits(img_bgr, result.masks.xy, result.boxes.xyxy.cpu().numpy())
            
            return True, inference_time, digits
            
        except Exception as e:
            return False, 0.0, []
    
    def extract_digits(self, image: np.ndarray, masks, boxes) -> List[np.ndarray]:
        """
        Extract all 9 digits from image in 3x3 grid order.
        
        Args:
            image: Source image
            masks: YOLO masks
            boxes: YOLO bounding boxes
            
        Returns:
            List of 9 cropped digit images (ordered: paslon1 digits, paslon2 digits, paslon3 digits)
        """
        # Organize detected objects
        detected_objects = []
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = map(int, box)
            detected_objects.append({
                'mask': masks[i],
                'center_y': (y1+y2)/2,
                'center_x': (x1+x2)/2
            })
        
        # Sort by Y position (top to bottom)
        detected_objects.sort(key=lambda k: k['center_y'])
        
        # Group into 3 rows (paslon 1, 2, 3)
        rows = []
        for i in range(0, 9, 3):
            chunk = detected_objects[i:i+3]
            if chunk:
                # Sort each row by X position (left to right)
                chunk.sort(key=lambda k: k['center_x'])
                rows.append(chunk)
        
        # Process each digit
        cropped_digits = []
        for row_idx, row in enumerate(rows):
            for digit_idx, obj in enumerate(row):
                try:
                    # Initial warp from mask
                    initial_warp = warp_from_mask_initial(image, obj['mask'])
                    
                    # Apply border processing
                    if self.border_mode == "with_border":
                        final_img = process_digit_with_border(initial_warp)
                    else:
                        final_img = process_digit_without_border(initial_warp)
                    
                    cropped_digits.append(final_img)
                    
                except Exception as e:
                    # Add empty image on failure
                    cropped_digits.append(np.zeros((64, 64, 3), dtype=np.uint8))
        
        return cropped_digits
    
    def save_digits(self, digits: List[np.ndarray], output_paths: List[str]) -> int:
        """
        Save cropped digits to files.
        
        Args:
            digits: List of cropped digit images
            output_paths: List of output file paths (must match digits length)
            
        Returns:
            Number of successfully saved digits
        """
        saved_count = 0
        
        for digit_img, output_path in zip(digits, output_paths):
            try:
                # Create output directory if needed
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                
                # Save image
                cv2.imwrite(output_path, digit_img)
                saved_count += 1
            except Exception as e:
                pass
        
        return saved_count
    
    def extract_paslon_rows(self, image_path: str) -> Tuple[bool, List[np.ndarray]]:
        """
        Extract paslon rows (3 digits combined per paslon).
        
        Args:
            image_path: Path to ROI image
            
        Returns:
            Tuple of (success, list of 3 paslon row images)
        """
        try:
            # Load image
            img_bgr = cv2.imread(image_path)
            if img_bgr is None:
                return False, []
            
            # YOLO inference
            results = self.model.predict(image_path, conf=0.25, iou=0.5, imgsz=1280, verbose=False)
            result = results[0]
            
            if result.masks is None:
                return False, []
            
            boxes = result.boxes.xyxy.cpu().numpy()
            
            # Organize detected objects with bounding boxes
            detected_objects = []
            for i, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box)
                detected_objects.append({
                    'box': box,
                    'center_y': (y1+y2)/2,
                    'center_x': (x1+x2)/2
                })
            
            # Sort by Y position (top to bottom)
            detected_objects.sort(key=lambda k: k['center_y'])
            
            # Group into 3 rows (paslon 1, 2, 3)
            rows = []
            for i in range(0, 9, 3):
                chunk = detected_objects[i:i+3]
                if chunk:
                    # Sort each row by X position (left to right)
                    chunk.sort(key=lambda k: k['center_x'])
                    rows.append(chunk)
            
            # Extract each paslon row
            paslon_rows = []
            for row in rows:
                if len(row) < 3:
                    # Not enough digits, skip
                    paslon_rows.append(np.zeros((64, 200, 3), dtype=np.uint8))
                    continue
                
                # Get bounding box from leftmost to rightmost digit
                leftmost_box = row[0]['box']  # First digit (leftmost)
                rightmost_box = row[2]['box']  # Third digit (rightmost)
                
                # Combined bounding box: left from first digit, right from last digit
                x1 = int(leftmost_box[0])
                y1 = int(min(leftmost_box[1], rightmost_box[1]))
                x2 = int(rightmost_box[2])
                y2 = int(max(leftmost_box[3], rightmost_box[3]))
                
                # Crop the row
                row_img = img_bgr[y1:y2, x1:x2]
                
                paslon_rows.append(row_img)
            
            return True, paslon_rows
            
        except Exception as e:
            return False, []
