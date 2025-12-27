"""Kawal Pemilu 2024 Scraper CLI - Main Entry Point."""

import sys
from cli_core import create_cli_injector, CLISettings


# Suppress asyncio errors on Windows
class StderrFilter:
    """Filter to suppress asyncio AssertionError spam on Windows."""
    
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = []
        
    def write(self, text):
        # Filter out asyncio AssertionError spam
        if 'AssertionError' in text and ('asyncio' in text or '_ProactorBaseWritePipeTransport' in text):
            return
        if 'Exception in callback' in text and '_ProactorBaseWritePipeTransport' in text:
            return
        if text.strip().startswith('handle: <Handle _ProactorBaseWritePipeTransport'):
            return
        if 'Traceback (most recent call last):' in text and len(self.buffer) > 0:
            if any('_ProactorBaseWritePipeTransport' in line for line in self.buffer[-5:]):
                return
        
        self.buffer.append(text)
        if len(self.buffer) > 20:
            self.buffer.pop(0)
            
        self.original_stderr.write(text)
        
    def flush(self):
        self.original_stderr.flush()


if sys.platform == 'win32':
    sys.stderr = StderrFilter(sys.stderr)


def download_workflow(injector):
    """Execute download workflow."""
    menu = injector.get_menu_service()
    download_service = injector.get_download_service()
    
    # Select download type
    download_type = menu.select_download_type()
    if not download_type:
        return
    
    # Select download mode
    download_mode = menu.select_download_mode()
    if not download_mode:
        return
    
    # Select location
    province_result = menu.select_province()
    if not province_result:
        return
    
    province_id, province_name = province_result
    
    regency_result = menu.select_regency(province_id)
    if not regency_result:
        return
    
    regency_id, regency_name = regency_result
    
    location_ids = {
        'province_id': province_id,
        'regency_id': regency_id
    }
    
    # If per-district mode, select district
    if download_mode == 'district':
        district_result = menu.select_district(regency_id)
        if not district_result:
            return
        
        district_id, district_name = district_result
        location_ids['district_id'] = district_id
    
    # Ask for verbose mode
    verbose = menu.select_verbose_mode()
    
    # Execute download
    download_service.execute_download(location_ids, download_type, verbose)


def autocrop_workflow(injector):
    """Execute auto-crop workflow."""
    autocrop_service = injector.get_autocrop_service()
    autocrop_service.execute()


def main():
    """Main CLI entry point."""
    # Create injector with default settings
    settings = CLISettings()
    injector = create_cli_injector(settings)
    
    try:
        while True:
            # Main menu
            menu = injector.get_menu_service()
            action = menu.select_main_action()
            
            if not action:
                break
            
            if action == 'download':
                download_workflow(injector)
            elif action == 'autocrop':
                autocrop_workflow(injector)
            
            # Ask if continue
            if not menu.confirm_action('\nLanjut ke menu utama?', default=True):
                break
    
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
