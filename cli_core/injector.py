"""Dependency injection container for CLI."""

from typing import Optional

from .config import CLISettings
from .utils import LocationDataProvider
from .services import MenuService, DownloadService, AutoCropService, ProgressService


class CLIInjector:
    """Dependency injection container for CLI services."""
    
    def __init__(self, settings: Optional[CLISettings] = None):
        """
        Initialize CLI injector.
        
        Args:
            settings: CLI settings (creates default if None)
        """
        self.settings = settings or CLISettings()
        self._data_provider = None
    
    def get_data_provider(self) -> LocationDataProvider:
        """Get location data provider (singleton)."""
        if self._data_provider is None:
            self._data_provider = LocationDataProvider(self.settings.context_path)
        return self._data_provider
    
    def get_menu_service(self) -> MenuService:
        """Get menu service."""
        data = self.get_data_provider()
        return MenuService(data)
    
    def get_progress_service(self) -> ProgressService:
        """Get progress service."""
        return ProgressService()
    
    def get_download_service(self) -> DownloadService:
        """Get download service."""
        progress = self.get_progress_service()
        return DownloadService(self.settings, progress)
    
    def get_autocrop_service(self) -> AutoCropService:
        """Get auto-crop service."""
        from jumlah_suara_extractor import create_injector
        
        extraction_injector = create_injector()
        menu = self.get_menu_service()
        progress = self.get_progress_service()
        
        return AutoCropService(extraction_injector, menu, progress)


def create_cli_injector(settings: Optional[CLISettings] = None) -> CLIInjector:
    """
    Factory function to create CLI injector.
    
    Args:
        settings: Optional settings (creates default if None)
        
    Returns:
        CLIInjector instance
    """
    return CLIInjector(settings)
