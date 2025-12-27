"""Menu service for interactive CLI prompts."""

import questionary
from typing import Dict, Optional, List, Tuple

from ..utils import clear_screen, print_header, LocationDataProvider


class MenuService:
    """Service for handling all interactive menu prompts."""
    
    def __init__(self, data_provider: LocationDataProvider):
        """
        Initialize menu service.
        
        Args:
            data_provider: Location data provider
        """
        self.data = data_provider
    
    def select_main_action(self) -> str:
        """
        Main menu: download or auto-crop.
        
        Returns:
            'download' or 'autocrop'
        """
        clear_screen()
        print_header("KAWAL PEMILU 2024 SCRAPER CLI")
        
        action = questionary.select(
            'Pilih Aksi',
            choices=[
                questionary.Choice('📥 Download Foto C1 Plano', value='download'),
                questionary.Choice('✂️  Auto Crop Jumlah Suara', value='autocrop')
            ]
        ).ask()
        
        return action
    
    def select_download_type(self) -> str:
        """
        Select download type: regular or ROI.
        
        Returns:
            'regular' or 'roi'
        """
        clear_screen()
        print_header("TIPE DOWNLOAD")
        
        download_type = questionary.select(
            'Pilih Tipe Download',
            choices=[
                questionary.Choice('Download Image Biasa (Full C1)', value='regular'),
                questionary.Choice('Download ROI (Region of Interest - KPU only)', value='roi')
            ]
        ).ask()
        
        return download_type
    
    def select_download_mode(self) -> str:
        """
        Select download mode: district or regency.
        
        Returns:
            'district' or 'regency'
        """
        clear_screen()
        print_header("MODE DOWNLOAD")
        
        mode = questionary.select(
            'Pilih Mode Download',
            choices=[
                questionary.Choice('Per Kecamatan', value='district'),
                questionary.Choice('Satu Kabupaten (Bulk)', value='regency')
            ]
        ).ask()
        
        return mode
    
    def select_verbose_mode(self) -> bool:
        """
        Ask if verbose mode should be enabled.
        
        Returns:
            True if verbose, False otherwise
        """
        verbose = questionary.select(
            'Aktifkan Log Verbose?',
            choices=[
                questionary.Choice('Tidak (Hanya Tampilkan Progress Bar)', value=False),
                questionary.Choice('Ya (Tampilkan Log Lengkap)', value=True)
            ]
        ).ask()
        
        return verbose
    
    def _paginated_select(self, message: str, items: Dict[str, str], page_size: int = 10) -> Optional[str]:
        """
        Paginated selection for large lists.
        
        Args:
            message: Prompt message
            items: Dict of {id: name}
            page_size: Items per page
            
        Returns:
            Selected ID or None
        """
        sorted_items = sorted(items.items(), key=lambda x: x[1])
        current_page = 0
        total_pages = (len(sorted_items) + page_size - 1) // page_size
        
        while True:
            clear_screen()
            start_idx = current_page * page_size
            end_idx = min(start_idx + page_size, len(sorted_items))
            
            current_items = sorted_items[start_idx:end_idx]
            
            choices = []
            if current_page > 0:
                choices.append(questionary.Choice('<- Halaman Sebelumnya', value='PREV'))
            
            for item_id, item_name in current_items:
                choices.append(questionary.Choice(item_name, value=item_id))
            
            if current_page < total_pages - 1:
                choices.append(questionary.Choice('Halaman Selanjutnya ->', value='NEXT'))
            
            result = questionary.select(
                f'{message} (Halaman {current_page + 1}/{total_pages})',
                choices=choices
            ).ask()
            
            if result == 'PREV':
                current_page -= 1
            elif result == 'NEXT':
                current_page += 1
            elif result is None:
                return None
            else:
                return result
    
    def select_province(self) -> Optional[Tuple[str, str]]:
        """
        Select province.
        
        Returns:
            Tuple of (province_id, province_name) or None
        """
        provinces = self.data.get_provinces()
        
        if not provinces:
            print("❌ Tidak ada provinsi ditemukan!")
            return None
        
        province_id = self._paginated_select('Pilih Provinsi', provinces)
        
        if province_id is None:
            return None
        
        return (province_id, provinces[province_id])
    
    def select_regency(self, province_id: str) -> Optional[Tuple[str, str]]:
        """
        Select regency in a province.
        
        Args:
            province_id: Province ID
            
        Returns:
            Tuple of (regency_id, regency_name) or None
        """
        regencies = self.data.get_regencies(province_id)
        
        if not regencies:
            print("❌ Tidak ada kabupaten ditemukan!")
            return None
        
        regency_id = self._paginated_select('Pilih Kabupaten/Kota', regencies)
        
        if regency_id is None:
            return None
        
        return (regency_id, regencies[regency_id])
    
    def select_district(self, regency_id: str) -> Optional[Tuple[str, str]]:
        """
        Select district in a regency.
        
        Args:
            regency_id: Regency ID
            
        Returns:
            Tuple of (district_id, district_name) or None
        """
        districts = self.data.get_districts(regency_id)
        
        if not districts:
            print("❌ Tidak ada kecamatan ditemukan!")
            return None
        
        district_id = self._paginated_select('Pilih Kecamatan', districts)
        
        if district_id is None:
            return None
        
        return (district_id, districts[district_id])
    
    def confirm_action(self, message: str, default: bool = True) -> bool:
        """
        Confirm an action.
        
        Args:
            message: Confirmation message
            default: Default choice
            
        Returns:
            True if confirmed, False otherwise
        """
        return questionary.confirm(message, default=default).ask()
