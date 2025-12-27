"""Dependency injection container for jumlah_suara_extractor."""

from typing import Optional

from .config import Settings
from .core import DigitCropper, WithBorderProcessor, WithoutBorderProcessor
from .services import ProvinceService, ExtractionService
from .utils import PerformanceTracker


def _lazy_import_yolo():
    """Lazy import YOLO to make ultralytics optional."""
    try:
        from ultralytics import YOLO
        return YOLO
    except ImportError:
        raise ImportError(
            "ultralytics is required for digit extraction features. "
            "Install it with: pipenv install -e \".[extraction]\""
        )


class Injector:
    """
    Simple dependency injection container.
    Manages creation and lifecycle of application dependencies.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize injector with settings.
        
        Args:
            settings: Application settings (creates default if None)
        """
        self.settings = settings or Settings()
        self._model_cache: Optional[object] = None  # YOLO instance (lazy loaded)
    
    def get_model(self):
        """
        Get YOLO model instance (singleton).
        
        Returns:
            YOLO model instance
            
        Raises:
            ImportError: If ultralytics is not installed
        """
        if self._model_cache is None:
            YOLO = _lazy_import_yolo()
            self._model_cache = YOLO(self.settings.model_path)
        return self._model_cache
    
    def get_border_processor(self, mode: str):
        """
        Get border processor based on mode.
        
        Args:
            mode: "with_border" or "without_border"
            
        Returns:
            Border processor instance
        """
        if mode == "with_border":
            return WithBorderProcessor(peel_pixels=self.settings.with_border_peel_pixels)
        else:
            return WithoutBorderProcessor(peel_pixels=self.settings.without_border_peel_pixels)
    
    def get_cropper(self, border_mode: str) -> DigitCropper:
        """
        Get DigitCropper with injected dependencies.
        
        Args:
            border_mode: "with_border" or "without_border"
            
        Returns:
            DigitCropper instance
        """
        model = self.get_model()
        processor = self.get_border_processor(border_mode)
        return DigitCropper(model, processor)
    
    def get_province_service(self) -> ProvinceService:
        """
        Get ProvinceService.
        
        Returns:
            ProvinceService instance
        """
        return ProvinceService(self.settings.output_roi_path)
    
    def get_extraction_service(
        self,
        border_mode: str,
        duplicate_mode: str,
        structure_type: str = "structured"
    ) -> ExtractionService:
        """
        Get ExtractionService with all dependencies.
        
        Args:
            border_mode: "with_border" or "without_border"
            duplicate_mode: "double" or "sequential"
            structure_type: "structured" or "flat"
            
        Returns:
            ExtractionService instance
        """
        cropper = self.get_cropper(border_mode)
        return ExtractionService(
            cropper=cropper,
            duplicate_mode=duplicate_mode,
            structure_type=structure_type
        )
    
    def get_performance_tracker(self) -> PerformanceTracker:
        """
        Get PerformanceTracker.
        
        Returns:
            PerformanceTracker instance
        """
        return PerformanceTracker()


def create_injector(settings: Optional[Settings] = None) -> Injector:
    """
    Factory function to create injector.
    
    Args:
        settings: Optional settings (creates default if None)
        
    Returns:
        Injector instance
    """
    return Injector(settings)
