"""Core interfaces and protocols for jumlah_suara_extractor."""

from abc import ABC, abstractmethod
from typing import Protocol, Tuple, List
import numpy as np


class BorderProcessor(Protocol):
    """Protocol for border processing strategies."""
    
    def process(self, img: np.ndarray) -> np.ndarray:
        """
        Process image to remove borders.
        
        Args:
            img: Input image
            
        Returns:
            Processed image with borders removed
        """
        ...


class ICropper(ABC):
    """Abstract interface for digit cropping."""
    
    @abstractmethod
    def process_image(self, image_path: str) -> Tuple[bool, float, List[np.ndarray]]:
        """
        Process single ROI image and extract all 9 digits.
        
        Args:
            image_path: Path to ROI image
            
        Returns:
            Tuple of (success, inference_time, list of cropped digit images)
        """
        pass
    
    @abstractmethod
    def extract_paslon_rows(self, image_path: str) -> Tuple[bool, List[np.ndarray]]:
        """
        Extract paslon rows (3 digits combined per paslon).
        
        Args:
            image_path: Path to ROI image
            
        Returns:
            Tuple of (success, list of 3 paslon row images)
        """
        pass
