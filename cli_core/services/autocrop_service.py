"""Auto-crop service for extraction workflow orchestration."""

import questionary
from typing import Optional

from ..utils import clear_screen, print_header


class AutoCropService:
    """Service for orchestrating auto-crop workflow."""
    
    def __init__(self, extraction_injector, menu_service, progress_service):
        """
        Initialize auto-crop service.
        
        Args:
            extraction_injector: Injector from jumlah_suara_extractor
            menu_service: Menu service for prompts
            progress_service: Progress service
        """
        self.extraction_injector = extraction_injector
        self.menu = menu_service
        self.progress = progress_service
    
    def execute(self):
        """Execute full auto-crop workflow."""
        from jumlah_suara_extractor.utils import scan_roi_images
        import random
        
        clear_screen()
        print_header("AUTO CROP JUMLAH SUARA - YOLOv11 SEGMENTATION")
        
        # Get province service
        province_service = self.extraction_injector.get_province_service()
        
        # Detect provinces
        print("🔍 Mendeteksi provinsi yang tersedia di folder output_roi...")
        provinces = province_service.detect_provinces()
        
        if not provinces:
            print("❌ Tidak ada provinsi yang ditemukan di folder output_roi!")
            print("   Jalankan download ROI terlebih dahulu.")
            input("\nTekan Enter untuk kembali...")
            return
        
        # Display provinces
        clear_screen()
        print_header("PROVINSI YANG TERSEDIA")
        for prov_name, total_imgs, total_tps in provinces:
            print(f"📍 {prov_name}")
            print(f"   - Total Gambar: {total_imgs}")
            print(f"   - Total TPS: {total_tps}")
            print()
        
        # Select province
        province_choices = [
            questionary.Choice(f"{prov_name} ({total_imgs} gambar, {total_tps} TPS)", 
                             value=prov_name)
            for prov_name, total_imgs, total_tps in provinces
        ]
        
        selected_province = questionary.select(
            'Pilih Provinsi untuk Di-crop',
            choices=province_choices
        ).ask()
        
        if not selected_province:
            return
        
        province_info = next((p for p in provinces if p[0] == selected_province), None)
        total_images = province_info[1] if province_info else 0
        
        # Border mode
        clear_screen()
        print(f"✅ Provinsi dipilih: {selected_province}")
        print(f"📊 Total gambar: {total_images}\n")
        
        border_mode = questionary.select(
            'Pilih Mode Border Processing',
            choices=[
                questionary.Choice('With Border (Recommended untuk digit dengan border tebal)', 
                                 value='with_border'),
                questionary.Choice('Without Border (Untuk digit tanpa border atau border tipis)', 
                                 value='without_border')
            ]
        ).ask()
        
        if not border_mode:
            return
        
        # Duplicate mode
        clear_screen()
        print(f"✅ Border Mode: {border_mode}\n")
        
        duplicate_mode = questionary.select(
            'Pilih Mode Penamaan untuk Digit Duplikat',
            choices=[
                questionary.Choice('Double Notation (9.jpg, 99.jpg, 999.jpg)', value='double'),
                questionary.Choice('Sequential (9_1.jpg, 9_2.jpg, 9_3.jpg)', value='sequential')
            ]
        ).ask()
        
        if not duplicate_mode:
            return
        
        # Performance preview
        clear_screen()
        print(f"✅ Duplicate Mode: {duplicate_mode}\n")
        print("⚡ Menjalankan benchmark performa...")
        print("   (Testing pada 5 gambar sample)\n")
        
        cropper = self.extraction_injector.get_cropper(border_mode)
        tracker = self.extraction_injector.get_performance_tracker()
        tracker.start()
        
        province_path = province_service.get_province_path(selected_province)
        all_images = scan_roi_images(province_path)
        sample_size = min(5, len(all_images))
        sample_images = random.sample(all_images, sample_size) if len(all_images) > sample_size else all_images
        
        for img_info in sample_images:
            image_path = img_info[0]
            success, inference_time, digits = cropper.process_image(image_path)
            tracker.record_image(success, inference_time, len(digits))
        
        tracker.display_preview_metrics(sample_size, total_images)
        
        # Confirm
        proceed = self.menu.confirm_action('Lanjutkan dengan auto-cropping?', default=True)
        if not proceed:
            return
        
        # Output structure
        clear_screen()
        structure_type = questionary.select(
            'Pilih Struktur Folder Output',
            choices=[
                questionary.Choice('Structured (Mirror struktur output_roi)', value='structured'),
                questionary.Choice('Flat (Semua digit dalam satu folder)', value='flat')
            ]
        ).ask()
        
        if not structure_type:
            return
        
        # Output folder
        output_base = questionary.text(
            'Nama folder output',
            default='output_digits'
        ).ask()
        
        if not output_base:
            return
        
        # Start processing
        clear_screen()
        print_header("MEMULAI AUTO-CROPPING")
        print(f"📂 Output: {output_base}/")
        print(f"📁 Struktur: {structure_type}")
        print(f"🎯 Border Mode: {border_mode}")
        print(f"🔢 Duplicate Mode: {duplicate_mode}")
        print("="*60)
        print()
        
        # Get extraction service
        extraction_service = self.extraction_injector.get_extraction_service(
            border_mode=border_mode,
            duplicate_mode=duplicate_mode,
            structure_type=structure_type
        )
        
        # Reset tracker
        tracker.reset()
        tracker.start()
        
        # Process with progress
        print("Processing images...")
        for item, update_status in self.progress.track_with_status(all_images, "Cropping"):
            saved_count = extraction_service.process_tps_image(item, output_base)
            
            if saved_count > 0:
                tracker.record_image(True, 0, saved_count)
                update_status(f"✓ Saved {saved_count} files")
            else:
                tracker.record_image(False, 0, 0)
                update_status("✗ Failed")
        
        # Display final metrics
        print()
        tracker.display_metrics()
        
        print(f"\n✅ Auto-cropping selesai!")
        print(f"📂 Output disimpan di: {output_base}/\n")
        
        input("Tekan Enter untuk kembali...")
