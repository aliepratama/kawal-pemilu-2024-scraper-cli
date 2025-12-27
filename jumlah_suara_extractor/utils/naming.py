from typing import Optional, Dict, Tuple
from collections import defaultdict


class DigitNamingTracker:
    """
    Tracks used digit filenames to handle duplicates.
    """
    
    def __init__(self, duplicate_mode: str = "double"):
        """
        Initialize the tracker.
        
        Args:
            duplicate_mode: "double" (9, 99, 999) or "sequential" (9_1, 9_2, 9_3)
        """
        self.duplicate_mode = duplicate_mode
        self.used_names: Dict[str, int] = defaultdict(int)
    
    def generate_filename(self, kode_kelurahan: str, nomor_tps: str, 
                         nomor_paslon: int, digit_value: str) -> str:
        """
        Generate unique filename for a digit, handling duplicates.
        
        Args:
            kode_kelurahan: Kode kelurahan (10 digits)
            nomor_tps: Nomor TPS (3 digits, zero-padded)
            nomor_paslon: Nomor paslon (1, 2, or 3)
            digit_value: The digit value ('0'-'9' or 'X')
            
        Returns:
            Complete filename: raw_<kode_kelurahan>_<nomor TPS>_<paslon>_<digit>.jpg
        """
        # Normalize X to 0 as per requirement
        if digit_value.upper() == 'X':
            digit_value = '0'
        
        # Create base key for duplicate tracking
        base_key = f"{kode_kelurahan}_{nomor_tps.zfill(3)}_{nomor_paslon}_{digit_value}"
        
        # Check if this digit has been used before
        occurrence = self.used_names[base_key]
        self.used_names[base_key] += 1
        
        # Generate filename based on duplicate mode
        if occurrence == 0:
            # First occurrence - just use the digit
            filename = f"raw_{kode_kelurahan}_{nomor_tps.zfill(3)}_{nomor_paslon}_{digit_value}.jpg"
        else:
            if self.duplicate_mode == "double":
                # Double notation: 9, 99, 999, etc.
                digit_suffix = digit_value * (occurrence + 1)
                filename = f"raw_{kode_kelurahan}_{nomor_tps.zfill(3)}_{nomor_paslon}_{digit_suffix}.jpg"
            else:  # sequential
                # Sequential: 9_1, 9_2, 9_3, etc.
                filename = f"raw_{kode_kelurahan}_{nomor_tps.zfill(3)}_{nomor_paslon}_{digit_value}_{occurrence + 1}.jpg"
        
        return filename
    
    def reset(self):
        """Reset the tracker for a new TPS."""
        self.used_names.clear()


def parse_roi_filename(filename: str) -> Optional[Tuple[str, str]]:
    """
    Parse ROI filename to extract kode_kelurahan and nomor_tps.
    
    Expected format: raw_<kode_kelurahan>_<nomor_tps>_<hash>.jpg
    Example: raw_6104122016_012_a8e35.jpg
    
    Args:
        filename: ROI filename
        
    Returns:
        Tuple of (kode_kelurahan, nomor_tps) or None if parsing fails
    """
    try:
        # Remove extension
        name_without_ext = filename.replace('.jpg', '').replace('.JPG', '')
        
        # Split by underscore
        parts = name_without_ext.split('_')
        
        # Validate format: raw_<kode>_<tps>_<hash>
        if len(parts) >= 4 and parts[0] == 'raw':
            kode_kelurahan = parts[1]
            nomor_tps = parts[2]
            
            # Validate kode_kelurahan is 10 digits
            if len(kode_kelurahan) == 10 and kode_kelurahan.isdigit():
                return (kode_kelurahan, nomor_tps)
        
        return None
    except Exception:
        return None


def format_tps_number(tps: str) -> str:
    """
    Format TPS number to 3-digit zero-padded string.
    
    Args:
        tps: TPS number (can be string or int)
        
    Returns:
        3-digit zero-padded string
    """
    try:
        tps_int = int(tps)
        return f"{tps_int:03d}"
    except:
        return str(tps).zfill(3)
