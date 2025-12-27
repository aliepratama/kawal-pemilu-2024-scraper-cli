"""CLI configuration settings."""

from dataclasses import dataclass
import os


@dataclass
class CLISettings:
    """CLI application settings."""
    
    # Data paths
    context_file: str = "cli_core/context/tps.json"
    
    # Output paths
    output_dir: str = "output"
    output_roi_dir: str = "output_roi"
    
    # Scrapy settings
    spider_name: str = "kawal_spider"
    scrapy_project: str = "kawal_pemilu_scraper"
    
    # Display settings
    clear_screen_enabled: bool = True
    
    @property
    def context_path(self) -> str:
        """Get absolute path to context file."""
        if os.path.isabs(self.context_file):
            return self.context_file
        return os.path.join(os.getcwd(), self.context_file)
