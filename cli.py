import json
import questionary
import os
import sys
import subprocess
import tempfile
from tqdm import tqdm
import time
import threading
import io

# Suppress asyncio AssertionError messages on Windows
class StderrFilter:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr
        self.buffer = []
        
    def write(self, text):
        # Filter out asyncio AssertionError spam
        if 'AssertionError' in text and ('asyncio' in text or '_ProactorBaseWritePipeTransport' in text):
            return  # Suppress this line
        if 'Exception in callback' in text and '_ProactorBaseWritePipeTransport' in text:
            return  # Suppress callback exception header
        if text.strip().startswith('handle: <Handle _ProactorBaseWritePipeTransport'):
            return  # Suppress handle line
        if 'Traceback (most recent call last):' in text and len(self.buffer) > 0:
            # Check if previous line was asyncio error
            if any('_ProactorBaseWritePipeTransport' in line for line in self.buffer[-5:]):
                return
        
        # Keep track of recent lines to detect error blocks
        self.buffer.append(text)
        if len(self.buffer) > 20:
            self.buffer.pop(0)
            
        self.original_stderr.write(text)
        
    def flush(self):
        self.original_stderr.flush()

if sys.platform == 'win32':
    sys.stderr = StderrFilter(sys.stderr)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_data(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def get_provinces(id2name):
    return {k: v for k, v in id2name.items() if len(k) == 2}

def get_regencies(id2name, province_id):
    return {k: v for k, v in id2name.items() if len(k) == 4 and k.startswith(province_id)}

def get_districts(id2name, regency_id):
    return {k: v for k, v in id2name.items() if len(k) == 6 and k.startswith(regency_id)}

def get_villages(id2name, district_id):
    return {k: v for k, v in id2name.items() if len(k) == 10 and k.startswith(district_id)}

def get_all_villages_in_regency(id2name, regency_id):
    return {k: v for k, v in id2name.items() if len(k) == 10 and k.startswith(regency_id)}

def paginated_prompt(message, choices, page_size=10):
    """
    Custom pagination for questionary choices.
    """
    current_page = 0
    while True:
        clear_screen()
        start_idx = current_page * page_size
        end_idx = start_idx + page_size
        
        current_choices = choices[start_idx:end_idx]
        
        # Add navigation options
        nav_choices = []
        if current_page > 0:
            nav_choices.append(questionary.Choice('<- Kembali', value='BACK'))
        
        for label, value in current_choices:
            nav_choices.append(questionary.Choice(label, value=value))
        
        if end_idx < len(choices):
            nav_choices.append(questionary.Choice('Selanjutnya ->', value='NEXT'))
            
        selection = questionary.select(
            f'{message} (Halaman {current_page + 1})',
            choices=nav_choices,
            use_indicator=True,
            style=questionary.Style([
                ('qmark', 'fg:#673ab7 bold'),       # token in front of the question
                ('question', 'bold'),               # question text
                ('answer', 'fg:#f44336 bold'),      # submitted answer text behind the question
                ('pointer', 'fg:#673ab7 bold'),     # pointer used in select and checkbox prompts
                ('highlighted', 'fg:#673ab7 bold'), # pointed-at choice in select and checkbox prompts
                ('selected', 'fg:#cc5454'),         # style for a selected item of a checkbox
                ('separator', 'fg:#cc5454'),        # separator in lists
                ('instruction', ''),                # user instructions for select, rawselect, checkbox
                ('text', ''),                       # plain text
                ('disabled', 'fg:#858585 italic')   # disabled choices for select and checkbox prompts
            ])
        ).ask()
        
        if not selection: return None
        
        if selection == 'NEXT':
            current_page += 1
        elif selection == 'BACK':
            current_page -= 1
        else:
            return selection

def main():
    clear_screen()
    print("==================================================")
    print("       KAWAL PEMILU 2024 SCRAPER CLI")
    print("==================================================")
    print("Aplikasi ini digunakan untuk mengunduh foto C1 Plano")
    print("dari website KawalPemilu.org secara otomatis.")
    print("Silakan ikuti instruksi di bawah ini.")
    print("==================================================\n")
    
    print('Memuat data wilayah...')
    try:
        data = load_data('context/tps.json')
    except FileNotFoundError:
        print('Error: context/tps.json tidak ditemukan.')
        return

    id2name = data.get('id2name', {})
    
    clear_screen()
    print("==================================================")
    print("       KAWAL PEMILU 2024 SCRAPER CLI")
    print("==================================================")
    print()
    
    # Select Download Type
    download_type = questionary.select(
        'Pilih Tipe Download',
        choices=[
            questionary.Choice('Download Image Biasa (Full C1)', value='regular'),
            questionary.Choice('Download ROI (Region of Interest - KPU only)', value='roi')
        ]
    ).ask()
    
    if not download_type: return
    
    clear_screen()
    print("==================================================")
    print("       KAWAL PEMILU 2024 SCRAPER CLI")
    print("==================================================")
    print()
    
    # Select Mode
    mode = questionary.select(
        'Pilih Mode Download',
        choices=[
            questionary.Choice('Per Kecamatan', value='district'),
            questionary.Choice('Satu Kabupaten (Bulk)', value='regency')
        ]
    ).ask()
    
    if not mode: return

    # Select Province
    provinces = get_provinces(id2name)
    province_choices = [(f'{v} ({k})', k) for k, v in sorted(provinces.items(), key=lambda item: item[1])]
    
    province_id = paginated_prompt('Pilih Provinsi', province_choices)
    if not province_id: return
    
    clear_screen()
    # Select Regency
    regencies = get_regencies(id2name, province_id)
    regency_choices = [(f'{v} ({k})', k) for k, v in sorted(regencies.items(), key=lambda item: item[1])]
    
    regency_id = paginated_prompt('Pilih Kabupaten/Kota', regency_choices)
    if not regency_id: return
    
    clear_screen()
    village_ids = []
    district_name = 'ALL'
    
    if mode == 'district':
        # Select District
        districts = get_districts(id2name, regency_id)
        district_choices = [(f'{v} ({k})', k) for k, v in sorted(districts.items(), key=lambda item: item[1])]
        
        district_id = paginated_prompt('Pilih Kecamatan', district_choices)
        if not district_id: return
        
        clear_screen()
        print(f'Selected District ID: {district_id}')
        villages = get_villages(id2name, district_id)
        village_ids = list(villages.keys())
        district_name = districts[district_id]
    else:
        # Bulk Regency
        clear_screen()
        print(f'Mengumpulkan data desa di {regencies[regency_id]}...')
        villages = get_all_villages_in_regency(id2name, regency_id)
        village_ids = list(villages.keys())
        district_name = 'ALL'

    print(f'Ditemukan {len(village_ids)} desa.')
    
    # Resume Detection - Check for existing district folders in output
    # Use different output folder based on download_type
    if mode == 'regency':
        output_folder = 'output_roi' if download_type == 'roi' else 'output'
        output_path = os.path.join(output_folder, provinces[province_id], regencies[regency_id])
        existing_districts = []
        
        if os.path.exists(output_path):
            # Get all directories in the regency output folder
            try:
                existing_folders = [f for f in os.listdir(output_path) if os.path.isdir(os.path.join(output_path, f))]
                
                # Map village IDs to their districts
                id2name_data = load_data('context/tps.json')
                id2name = id2name_data.get('id2name', {})
                
                # Group villages by district
                district_to_villages = {}
                for vid in village_ids:
                    district_id = vid[:6] if len(vid) == 10 else ''
                    district_name = id2name.get(district_id, 'UNKNOWN')
                    if district_name not in district_to_villages:
                        district_to_villages[district_name] = []
                    district_to_villages[district_name].append(vid)
                
                # Find which districts already exist in output
                for folder_name in existing_folders:
                    if folder_name in district_to_villages:
                        existing_districts.append(folder_name)
                
                if existing_districts:
                    clear_screen()
                    print(f'Ditemukan {len(existing_districts)} kecamatan yang sudah pernah didownload:')
                    for dist in sorted(existing_districts):
                        village_count = len(district_to_villages[dist])
                        print(f'  - {dist} ({village_count} desa)')
                    print()
                    
                    skip_existing = questionary.select(
                        'Apakah ingin skip kecamatan yang sudah didownload?',
                        choices=[
                            questionary.Choice('Ya (Skip kecamatan yang sudah ada)', value=True),
                            questionary.Choice('Tidak (Download ulang semua)', value=False)
                        ]
                    ).ask()
                    
                    if skip_existing:
                        # Filter out villages from existing districts
                        original_count = len(village_ids)
                        village_ids = [vid for vid in village_ids 
                                     if id2name.get(vid[:6], '') not in existing_districts]
                        skipped_count = original_count - len(village_ids)
                        print(f'\nSkip {skipped_count} desa dari {len(existing_districts)} kecamatan.')
                        print(f'Akan download {len(village_ids)} desa dari kecamatan lainnya.\n')
                        
                        if len(village_ids) == 0:
                            print('Semua kecamatan sudah didownload. Tidak ada yang perlu didownload.')
                            return
            except Exception as e:
                print(f'Warning: Gagal mengecek folder output: {e}')
    
    # Verbose Mode
    verbose = questionary.select(
        'Aktifkan Log Verbose?',
        choices=[
            questionary.Choice('Tidak (Hanya Tampilkan Progress Bar)', value=False),
            questionary.Choice('Ya (Tampilkan Log Lengkap)', value=True)
        ]
    ).ask()

    # Run Scrapy
    print('Memulai Scraper...')
    
    # Create a temp file for village IDs to avoid command line length limits
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write(','.join(village_ids))
        tmp_path = tmp.name
    
    try:
        # Set output folder based on download type
        output_folder = 'output_roi' if download_type == 'roi' else 'output'
        
        # CRITICAL: Create output folder if not exists
        os.makedirs(output_folder, exist_ok=True)
        
        cmd = [
            'scrapy', 'crawl', 'kawal_spider',
            '-a', f'village_ids_file={tmp_path}',
            '-a', f'district_name={district_name}',
            '-a', f'download_type={download_type}',
            '-a', f'regency_name={regencies[regency_id]}',
            '-a', f'province_name={provinces[province_id]}',
            '-a', f'verbose={str(verbose)}',
            '-s', f'IMAGES_STORE={output_folder}'
        ]
        
        if not verbose:
            # Suppress logs
            cmd.extend(['-s', 'LOG_LEVEL=ERROR'])
        
        # Set environment for unbuffered output
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE if not verbose else None, # If verbose, let stderr flow to console
            text=True,
            bufsize=1,
            encoding='utf-8',
            env=env
        )
        
        if not verbose:
            # Progress Bar Logic with dynamic district/village display
            pbar = tqdm(
                total=len(village_ids), 
                unit='desa', 
                desc='Download', 
                bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
                ncols=100,
                miniters=1,
                mininterval=0
            )
            
            current_progress = ''
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    if '[PROGRESS]' in line:
                        # Extract district and village name from progress marker
                        # Format: [PROGRESS] DISTRICT_NAME > VILLAGE_NAME
                        try:
                            progress_text = line.split('[PROGRESS]')[1].strip()
                            if progress_text != current_progress:
                                current_progress = progress_text
                                # Truncate if too long
                                display_text = progress_text[:40] + '...' if len(progress_text) > 40 else progress_text
                                pbar.set_description(f'Download [{display_text}]')
                                pbar.refresh()
                        except Exception as e:
                            pass
                        pbar.update(1)
            
            pbar.close()
            
            # Check for errors in stderr if process failed
            if process.returncode != 0:
                print('\nScraper finished with errors.')
                stderr_output = process.stderr.read()
                if stderr_output:
                    print('Error details:')
                    print(stderr_output)
        else:
            process.wait()
            
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == '__main__':
    main()
