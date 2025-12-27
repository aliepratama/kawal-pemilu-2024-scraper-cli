"""Province detection service."""

import os
from typing import List, Tuple


class ProvinceService:
    """Service for detecting and managing provinces in output_roi folder."""
    
    def __init__(self, output_roi_path: str = "output_roi"):
        """
        Initialize province service.
        
        Args:
            output_roi_path: Path to output_roi folder
        """
        self.output_roi_path = output_roi_path
    
    def detect_provinces(self) -> List[Tuple[str, int, int]]:
        """
        Scans output_roi folder and returns list of available provinces with statistics.
        
        Returns:
            List of tuples: [(province_name, total_images, total_tps)]
        """
        if not os.path.exists(self.output_roi_path):
            return []
        
        provinces = []
        
        for province_name in os.listdir(self.output_roi_path):
            province_path = os.path.join(self.output_roi_path, province_name)
            
            if not os.path.isdir(province_path):
                continue
            
            # Count total JPG images in province
            total_images = 0
            tps_set = set()
            
            # Recursively scan all subdirectories
            for root, dirs, files in os.walk(province_path):
                for file in files:
                    if file.lower().endswith('.jpg'):
                        total_images += 1
                        
                        # Extract TPS from filename
                        try:
                            parts = file.split('_')
                            if len(parts) >= 3 and parts[0] == 'raw':
                                kode_kelurahan = parts[1]
                                tps = parts[2]
                                tps_identifier = f"{kode_kelurahan}_{tps}"
                                tps_set.add(tps_identifier)
                        except:
                            pass
            
            if total_images > 0:
                provinces.append((province_name, total_images, len(tps_set)))
        
        # Sort by province name
        provinces.sort(key=lambda x: x[0])
        
        return provinces
    
    def get_province_path(self, province_name: str) -> str:
        """
        Get full path to a province folder.
        
        Args:
            province_name: Name of the province
            
        Returns:
            Full path to province folder
        """
        return os.path.join(self.output_roi_path, province_name)
