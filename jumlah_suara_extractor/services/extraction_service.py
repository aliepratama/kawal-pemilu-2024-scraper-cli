"""Main extraction service for orchestrating digit cropping workflow."""

import os
import cv2
from typing import Tuple, List

from ..core import DigitCropper
from ..utils import (
    DigitNamingTracker,
    format_tps_number,
    create_output_structure,
    PerformanceTracker
)


class ExtractionService:
    """
    High-level service for extraction workflow.
    Coordinates cropper, file operations, and naming.
    """
    
    def __init__(
        self,
        cropper: DigitCropper,
        duplicate_mode: str = "double",
        structure_type: str = "structured"
    ):
        """
        Initialize extraction service.
        
        Args:
            cropper: DigitCropper instance
            duplicate_mode: "double" or "sequential"
            structure_type: "structured" or "flat"
        """
        self.cropper = cropper
        self.duplicate_mode = duplicate_mode
        self.structure_type = structure_type
    
    def process_tps_image(
        self,
        img_info: Tuple[str, str, str, str, str, str, str],
        output_base: str
    ) -> int:
        """
        Process single TPS image and save all outputs.
        
        Args:
            img_info: Tuple of (image_path, province, regency, district, village, kode_kelurahan, nomor_tps)
            output_base: Base output directory
            
        Returns:
            Number of files saved
        """
        image_path, province, regency, district, village, kode_kelurahan, nomor_tps = img_info
        
        # Process image for individual digits
        success, inference_time, digits = self.cropper.process_image(image_path)
        
        # Also extract paslon rows
        paslon_success, paslon_rows = self.cropper.extract_paslon_rows(image_path)
        
        saved_count = 0
        
        if success and len(digits) == 9:
            # Create output directory
            output_dir = create_output_structure(
                output_base, self.structure_type,
                province, regency, district, village
            )
            
            # Create naming tracker for this TPS
            naming_tracker = DigitNamingTracker(self.duplicate_mode)
            
            # Generate output paths for all 9 digits
            output_paths = []
            for paslon_idx in range(3):  # 3 paslons
                paslon_num = paslon_idx + 1
                for digit_idx in range(3):  # 3 digits per paslon
                    digit_value = f"pos{digit_idx + 1}"  # pos1, pos2, pos3
                    
                    filename = naming_tracker.generate_filename(
                        kode_kelurahan,
                        format_tps_number(nomor_tps),
                        paslon_num,
                        digit_value
                    )
                    
                    output_path = os.path.join(output_dir, filename)
                    output_paths.append(output_path)
            
            # Save all individual digits
            for digit_img, output_path in zip(digits, output_paths):
                try:
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    cv2.imwrite(output_path, digit_img)
                    saved_count += 1
                except:
                    pass
            
            # Save paslon rows (3 digits combined per paslon)
            if paslon_success and len(paslon_rows) == 3:
                for paslon_idx, paslon_img in enumerate(paslon_rows):
                    paslon_num = paslon_idx + 1
                    paslon_filename = f"raw_{kode_kelurahan}_{format_tps_number(nomor_tps)}_{paslon_num}.jpg"
                    paslon_output_path = os.path.join(output_dir, paslon_filename)
                    
                    try:
                        cv2.imwrite(paslon_output_path, paslon_img)
                        saved_count += 1
                    except:
                        pass
        
        return saved_count
