import os
from pathlib import Path
from typing import List, Tuple


def detect_provinces(output_roi_path: str = "output_roi") -> List[Tuple[str, int, int]]:
    """
    Scans output_roi folder and returns list of available provinces with statistics.
    
    Args:
        output_roi_path: Path to output_roi folder
        
    Returns:
        List of tuples: [(province_name, total_images, total_tps)]
    """
    if not os.path.exists(output_roi_path):
        return []
    
    provinces = []
    
    for province_name in os.listdir(output_roi_path):
        province_path = os.path.join(output_roi_path, province_name)
        
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
                    
                    # Extract TPS from filename (format: raw_<kode_kelurahan>_<tps>_<hash>.jpg)
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


def get_province_path(output_roi_path: str, province_name: str) -> str:
    """
    Get full path to a province folder.
    
    Args:
        output_roi_path: Path to output_roi folder
        province_name: Name of the province
        
    Returns:
        Full path to province folder
    """
    return os.path.join(output_roi_path, province_name)
