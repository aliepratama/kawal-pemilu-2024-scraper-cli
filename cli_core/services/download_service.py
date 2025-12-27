"""Download service for managing scraping workflow."""

import subprocess
import os
from typing import Dict, Optional

from ..config import CLISettings
from .progress_service import ProgressService


class DownloadService:
    """Service for orchestrating download workflow with Scrapy."""
    
    def __init__(self, settings: CLISettings, progress: ProgressService):
        """
        Initialize download service.
        
        Args:
            settings: CLI settings
            progress: Progress service
        """
        self.settings = settings
        self.progress = progress
    
    def execute_download(
        self,
        location_ids: Dict[str, str],
        download_type: str,
        verbose: bool = False
    ):
        """
        Execute scrapy download.
        
        Args:
            location_ids: Dict with 'province_id', 'regency_id', optional 'district_id'
            download_type: 'regular' or 'roi'
            verbose: Enable verbose logging
        """
        # Prepare scrapy command
        cmd = [
            'scrapy', 'crawl', self.settings.spider_name,
            '-a', f"download_type={download_type}",
            '-a', f"province_id={location_ids['province_id']}",
            '-a', f"regency_id={location_ids['regency_id']}"
        ]
        
        if 'district_id' in location_ids:
            cmd.extend(['-a', f"district_id={location_ids['district_id']}"])
        
        # Log level
        if not verbose:
            cmd.extend(['--nolog'])
        
        # Set environment for unbuffered output
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        print(f"\n🚀 Starting download...")
        print(f"   Type: {download_type}")
        print(f"   Location: {location_ids}")
        print()
        
        # Run scrapy subprocess
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                universal_newlines=True,
                bufsize=1
            )
            
            # Stream output
            for line in iter(process.stdout.readline, ''):
                if line:
                    print(line.rstrip())
            
            process.wait()
            
            if process.returncode == 0:
                print("\n✅ Download selesai!")
            else:
                print(f"\n❌ Download gagal dengan kode: {process.returncode}")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
