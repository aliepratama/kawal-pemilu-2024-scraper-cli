# Kawal Pemilu 2024 Scraper CLI

CLI tool untuk mengunduh foto C1 Plano dan ROI (Region of Interest) dari website [KawalPemilu.org](https://kawalpemilu.org) secara otomatis menggunakan Scrapy dan Playwright.

## Features

### Download Modes
- **Regular C1 Images**: Download foto C1 Plano lengkap (full scan)
- **ROI Images**: Download cropped regions berisi vote counts (Region of Interest)

### Download Scope
- **Per Kecamatan**: Download satu kecamatan saja
- **Bulk (Satu Kabupaten)**: Download seluruh kabupaten sekaligus

### Advanced Features
- ✅ **Resume Detection**: Otomatis detect kecamatan yang sudah didownload dan skip
- ✅ **Real-time Progress**: Progress bar dengan status kecamatan/desa yang sedang diproses
- ✅ **Smart Folder Structure**: Organize by `PROVINSI/KABUPATEN/KECAMATAN/DESA/`
- ✅ **Separate Output**: Regular images → `output/`, ROI images → `output_roi/`
- ✅ **Windows Compatible**: Suppressed asyncio errors untuk Windows stability

## Installation

### Prerequisites
- Python 3.8+
- Pipenv (install via `pip install pipenv`)

### Setup

1. Clone repository:
```bash
git clone <repository-url>
cd kawal-pemilu-2024-scraper-cli
```

2. Install dependencies:
```bash
pipenv install
```

3. **Verify Playwright package is installed:**
```bash
# Check if playwright is in the dependencies
pipenv run pip list | grep playwright
```

If you don't see `playwright` in the list, install it manually:
```bash
pipenv install playwright
```

4. Install Playwright browsers:
```bash
pipenv run playwright install chromium
```

> **Important:** Steps 2-4 must be run on **every new machine/environment**. Playwright browsers are installed locally per environment.

### Verify Installation

Test if everything is installed correctly:
```bash
pipenv run python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

If successful, you'll see `Playwright OK`.

## Usage

### Basic Command
```bash
pipenv run python cli.py
```

### Interactive Flow

1. **Select Download Type**
   ```
   ? Pilih Tipe Download
     > Download Image Biasa (Full C1)
       Download ROI (Region of Interest - KPU only)
   ```

2. **Select Download Mode**
   ```
   ? Pilih Mode Download
     > Per Kecamatan
       Satu Kabupaten (Bulk)
   ```

3. **Select Location**
   - Choose Province → Regency → (District if per-kecamatan)

4. **Resume Detection** (Bulk mode only)
   ```
   Ditemukan 5 kecamatan yang sudah pernah didownload:
     - AIR UPAS (6 desa)
     - BENUA KAYONG (11 desa)
   
   ? Apakah ingin skip kecamatan yang sudah didownload?
     > Ya (Skip kecamatan yang sudah ada)
       Tidak (Download ulang semua)
   ```

5. **Verbose Mode**
   ```
   ? Aktifkan Log Verbose?
     > Tidak (Hanya Tampilkan Progress Bar)
       Ya (Tampilkan Log Lengkap)
   ```

### Progress Display

**Non-verbose mode** (recommended):
```
Download [AIR UPAS > SARI BEKAYAS]: 15%|███| 82/545 [01:23<07:45]
```

**Verbose mode** (for debugging):
```
2025-12-26 14:15:09 [kawal_spider] INFO: Found 13 ROI photos for AIR UPAS > AIR UPAS
```

## Output Structure

### Regular C1 Images
```
output/
├── KALIMANTAN BARAT/
│   └── KETAPANG/
│       ├── AIR UPAS/
│       │   ├── AIR UPAS/
│       │   │   ├── raw_6104212001_001_12345.jpg
│       │   │   └── raw_6104212001_002_12346.jpg
│       │   └── SARI BEKAYAS/
│       └── BENUA KAYONG/
```

### ROI Images
```
output_roi/
├── KALIMANTAN BARAT/
│   └── KETAPANG/
│       ├── AIR UPAS/
│       │   ├── AIR UPAS/
│       │   │   ├── raw_6104212001_001_67890.webp
│       │   │   └── raw_6104212001_002_67891.webp
```

## Technical Details

### Architecture
- **Scrapy**: Web scraping framework
- **Playwright**: Browser automation for JavaScript rendering
- **Questionary**: Interactive CLI prompts
- **TQDM**: Progress bar display

### ROI Image Extraction
ROI images are extracted from `div` element `id` attributes containing Google Cloud Storage URLs:
```
https://storage.googleapis.com/kawalc1/static/2024/transformed/{location_id}/{tps}/extracted/{hash}=s1280~paslon.webp
```

URLs are automatically decoded (`%3D` → `=`) to prevent double-encoding issues in Scrapy pipeline.

### Resume Detection Logic
1. Scans output folder for existing district directories
2. Groups villages by district from village IDs (first 6 digits)
3. Offers option to skip completed districts
4. Filters village list to exclude skipped districts

### Progress Tracking
- Progress markers: `[PROGRESS] DISTRICT > VILLAGE`
- Unbuffered output: `PYTHONUNBUFFERED=1`
- Real-time tqdm updates with district/village info
- Always prints even when no photos found

## Troubleshooting

### 'playwright' is not recognized

**Error:**
```
'playwright' is not recognized as an internal or external command
```

**Solution:**
This means Playwright package hasn't been installed. Follow these steps **in order**:

```bash
# Step 1: Make sure you're in the project directory
cd kawal-pemilu-2024-scraper-cli

# Step 2: Verify virtual environment exists
pipenv --venv
# Should show a path like: C:\Users\...\virtualenvs\kawal-pemilu-...

# Step 3: Install dependencies from Pipfile
pipenv install

# Step 4: Verify playwright package is installed
pipenv run pip list | findstr playwright
# Should show: playwright x.x.x

# Step 5: If playwright is NOT in the list, install it explicitly
pipenv install playwright

# Step 6: Now install Playwright browsers
pipenv run playwright install chromium

# Step 7: Verify installation
pipenv run python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

**Important:** ALWAYS use `pipenv run` prefix when running commands in this project.

### Playwright Installation Issues

If `playwright install` fails:
```bash
# Force reinstall
pipenv run playwright install --force chromium

# Or install all browsers
pipenv run playwright install
```

### Dependencies Not Found

If you get import errors after cloning on a new machine:
```bash
# Recreate virtual environment
pipenv --rm
pipenv install
pipenv run playwright install chromium
```

## Development

### Project Structure
```
kawal-pemilu-2024-scraper-cli/
├── cli.py                          # Main CLI interface
├── context/
│   └── tps.json                    # Location and ID mappings
├── kawal_pemilu_scraper/
│   ├── spiders/
│   │   └── kawal_spider.py         # Main spider logic
│   ├── pipelines.py                # Image download pipeline
│   ├── settings.py                 # Scrapy settings
│   └── middlewares.py              # Custom middlewares
├── output/                         # Regular C1 images
├── output_roi/                     # ROI images
└── README.md
```

### Key Components

**Spider (`kawal_spider.py`)**:
- Async `start()` method (Scrapy 2.13+)
- Conditional extraction: regular vs ROI
- District name mapping from village IDs
- URL decoding for ROI images

**CLI (`cli.py`)**:
- Interactive prompts (questionary)
- Resume detection logic
- Progress bar management (tqdm)
- Subprocess management with unbuffered output

**Settings (`settings.py`)**:
- AsyncIO policy for Windows
- Playwright configuration
- Image pipeline settings
- Concurrent requests tuning

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Data source: [KawalPemilu.org](https://kawalpemilu.org)
- Built with [Scrapy](https://scrapy.org/) and [Playwright](https://playwright.dev/)
