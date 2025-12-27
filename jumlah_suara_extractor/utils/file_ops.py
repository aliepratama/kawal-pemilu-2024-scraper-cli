import os
from pathlib import Path
from typing import List, Tuple, Optional
from .naming import parse_roi_filename


def create_output_structure(base_output: str, structure_type: str,
                           province: str = "", regency: str = "",
                           district: str = "", village: str = "") -> str:
    """
    Create appropriate output directory based on structure type.
    
    Args:
        base_output: Base output folder path
        structure_type: "structured" or "flat"
        province: Province name
        regency: Regency name
        district: District name
        village: Village name
        
    Returns:
        Full path to output directory
    """
    if structure_type == "structured":
        # Mirror output_roi hierarchy: base/province/regency/district/village
        parts = [base_output]
        if province:
            parts.append(province)
        if regency:
            parts.append(regency)
        if district:
            parts.append(district)
        if village:
            parts.append(village)
        
        output_path = os.path.join(*parts)
    else:  # flat
        # All in base output folder
        output_path = base_output
    
    # Create directory if it doesn't exist
    os.makedirs(output_path, exist_ok=True)
    
    return output_path


def scan_roi_images(province_path: str) -> List[Tuple[str, str, str, str, str, str, str]]:
    """
    Recursively scan all ROI images in province folder.
    
    Args:
        province_path: Full path to province folder in output_roi
        
    Returns:
        List of tuples: [(image_path, province, regency, district, village, kode_kelurahan, nomor_tps)]
    """
    images = []
    
    # Get province name from path
    province_name = os.path.basename(province_path)
    
    # Walk through directory structure
    for root, dirs, files in os.walk(province_path):
        for file in files:
            if file.lower().endswith('.jpg'):
                image_path = os.path.join(root, file)
                
                # Parse filename to get kode_kelurahan and nomor_tps
                parsed = parse_roi_filename(file)
                if parsed:
                    kode_kelurahan, nomor_tps = parsed
                    
                    # Extract hierarchy from path
                    # Structure: output_roi/PROVINCE/REGENCY/DISTRICT/VILLAGE/file.jpg
                    rel_path = os.path.relpath(root, province_path)
                    path_parts = rel_path.split(os.sep)
                    
                    regency = path_parts[0] if len(path_parts) > 0 and path_parts[0] != '.' else ""
                    district = path_parts[1] if len(path_parts) > 1 else ""
                    village = path_parts[2] if len(path_parts) > 2 else ""
                    
                    images.append((
                        image_path,
                        province_name,
                        regency,
                        district,
                        village,
                        kode_kelurahan,
                        nomor_tps
                    ))
    
    return images


def get_total_roi_images(province_path: str) -> int:
    """
    Count total ROI images in a province folder.
    
    Args:
        province_path: Full path to province folder
        
    Returns:
        Total number of JPG images
    """
    count = 0
    for root, dirs, files in os.walk(province_path):
        for file in files:
            if file.lower().endswith('.jpg'):
                count += 1
    return count
