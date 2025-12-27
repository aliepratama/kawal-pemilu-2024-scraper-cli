"""Configuration settings for jumlah_suara_extractor."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    """Application settings and configuration."""
    
    # Model configuration
    model_path: str = "jumlah_suara_extractor/weights/best.pt"
    yolo_conf: float = 0.25
    yolo_iou: float = 0.5
    yolo_imgsz: int = 1280
    
    # Path configuration
    output_roi_path: str = "output_roi"
    default_output_path: str = "output_digits"
    
    # Processing configuration
    with_border_peel_pixels: int = 6
    without_border_peel_pixels: int = 7
    
    # Performance configuration
    benchmark_sample_size: int = 5
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'Settings':
        """Create Settings from dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__dataclass_fields__})
