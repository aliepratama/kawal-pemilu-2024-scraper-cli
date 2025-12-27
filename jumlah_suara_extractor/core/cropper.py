"""Digit cropper with dependency injection."""

import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Tuple
import time

from .interfaces import BorderProcessor
from .processors import warp_from_mask_initial


class DigitCropper:
    """
    Main class for cropping vote number digits using YOLOv11-seg.
    Uses dependency injection for border processing strategy.
    """
    
    def __init__(self, model: YOLO, border_processor: BorderProcessor):
        """
        Initialize DigitCropper with injected dependencies.
        
        Args:
            model: YOLO model instance
            border_processor: Border processing strategy
        """
        self.model = model
        self.border_processor = border_processor
    
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
            digits = self._extract_digits(img_bgr, result.masks.xy, result.boxes.xyxy.cpu().numpy())
            
            return True, inference_time, digits
            
        except Exception as e:
            return False, 0.0, []
    
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
                leftmost_box = row[0]['box']
                rightmost_box = row[2]['box']
                
                # Combined bounding box
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
    
    def _extract_digits(self, image: np.ndarray, masks, boxes) -> List[np.ndarray]:
        """
        Extract all 9 digits from image in 3x3 grid order.
        
        Args:
            image: Source image
            masks: YOLO masks
            boxes: YOLO bounding boxes
            
        Returns:
            List of 9 cropped digit images
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
                    
                    # Apply border processing using injected processor
                    final_img = self.border_processor.process(initial_warp)
                    
                    cropped_digits.append(final_img)
                    
                except Exception as e:
                    # Add empty image on failure
                    cropped_digits.append(np.zeros((64, 64, 3), dtype=np.uint8))
        
        return cropped_digits
