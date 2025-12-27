# Kawal Pemilu 2024 Scraper CLI

CLI tool untuk mengunduh foto C1 Plano dan ROI (Region of Interest) dari website [KawalPemilu.org](https://kawalpemilu.org) secara otomatis menggunakan Scrapy dan Playwright.

## Features

### Download Modes
- **Regular C1 Images**: Download foto C1 Plano lengkap (full scan)
- **ROI Images**: Download cropped regions berisi vote counts (Region of Interest)

### Download Scope
- **Per Kecamatan**: Download satu kecamatan saja
- **Bulk (Satu Kabupaten)**: Download seluruh kabupaten sekaligus

### Auto-Cropping (NEW ✨)
- **Digit Extraction**: Automatic cropping of individual vote digits using YOLOv11 segmentation
- **Paslon Rows**: Extract combined 3-digit images per candidate
- **Border Processing**: Two modes (with/without border) for different digit styles
- **Modular Architecture**: Dependency injection pattern for extensibility
- **Performance Metrics**: Real-time benchmarking and progress tracking

### Architecture Highlights (NEW 🎯)
- ✅ **Modular CLI**: Refactored from 600+ to 130 lines using service-oriented architecture
- ✅ **Dependency Injection**: Clean separation of concerns with DI pattern
- ✅ **Service Layer**: MenuService, DownloadService, AutoCropService, ProgressService
- ✅ **Lazy Loading**: Optional dependencies loaded only when needed
- ✅ **Docker Support**: Two Dockerfiles (core-only and full-featured)

### Advanced Features
- ✅ **Resume Detection**: Otomatis detect kecamatan yang sudah didownload dan skip
- ✅ **Real-time Progress**: Progress bar dengan status kecamatan/desa yang sedang diproses
- ✅ **Smart Folder Structure**: Organize by `PROVINSI/KABUPATEN/KECAMATAN/DESA/`
- ✅ **Separate Output**: Regular images → `output/`, ROI images → `output_roi/`, Digits → `output_digits/`
- ✅ **Windows Compatible**: Suppressed asyncio errors untuk Windows stability

## Installation

### Prerequisites
- Python 3.12+
- Pipenv (install via `pip install pipenv`)

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd kawal-pemilu-2024-scraper-cli

# Install core dependencies only (scraping features)
pipenv install

# Install Playwright browsers
pipenv run playwright install chromium
```

### Installation Options

Project ini menggunakan **modular dependencies** - install hanya package yang Anda butuhkan:

#### 1️⃣ Core Only (Scraping Features)
```bash
pipenv install
```
**Includes**: scrapy, questionary, tqdm, playwright  
**Use for**: Download C1/ROI images only

#### 2️⃣ With Auto-Cropping Features
```bash
pipenv install -e ".[extraction]"
```
**Includes**: Core + ultralytics, opencv-python, numpy, torch  
**Use for**: Download + auto-crop vote digits

#### 3️⃣ Development (All Features)
```bash
pipenv install --dev
```
**Includes**: Core + extraction + pytest, black, flake8  
**Use for**: Development and testing

### Post-Installation

After installing dependencies, install Playwright browsers:
```bash
pipenv run playwright install chromium
```

### Verify Installation

Test if everything works:
```bash
# Test Playwright
pipenv run python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"

# Test extraction features (optional, if installed)
pipenv run python -c "from jumlah_suara_extractor import create_injector; print('Extraction OK')"
```

### Docker Setup (Alternative)

Project menyediakan **2 Docker images** untuk kebutuhan berbeda:

#### Option 1: Core Only (Scraping Features)
```bash
# Build lightweight image (~500MB)
docker-compose build

# Run interactively
docker-compose run --rm scraper
```

#### Option 2: Full Features (With Auto-Crop)
```bash
# Build complete image with YOLO (~2GB+)
docker build -f Dockerfile.extraction -t kawal-pemilu-scraper:extraction .

# Run with all features
docker run -it --rm \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/output_roi:/app/output_roi \
  -v $(pwd)/output_digits:/app/output_digits \
  -v $(pwd)/cli_core/context:/app/cli_core/context:ro \
  kawal-pemilu-scraper:extraction
```

> **Important:** Always use `docker-compose run` or `docker run -it` for interactive questionary prompts.

**See [DOCKER.md](DOCKER.md) for comprehensive Docker documentation.**

**Advantages:**
- ✅ No need to install Python, Pipenv, or Playwright locally
- ✅ Consistent environment across all machines
- ✅ Easy cleanup and image management
- ✅ Choose lightweight (core) or full-featured (extraction) setup

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

### Auto-Cropping Workflow (NEW ✨)

Setelah download ROI images, Anda bisa auto-crop digit angka suara:

1. **Run CLI dan pilih Auto Crop**
   ```bash
   pipenv run python cli.py
   ```
   Pilih: `✂️  Auto Crop Jumlah Suara`

2. **Select Province**
   - Sistem otomatis detect provinsi yang tersedia di `output_roi/`
   - Pilih provinsi yang ingin di-crop

3. **Border Mode**
   - **With Border**: Untuk digit dengan border tebal
   - **Without Border**: Untuk digit tanpa border/border tipis

4. **Duplicate Naming**
   - **Double notation**: `9.jpg, 99.jpg, 999.jpg`
   - **Sequential**: `9_1.jpg, 9_2.jpg, 9_3.jpg`

5. **Performance Preview**
   - Benchmark pada 5 sample images
   - Review estimasi waktu total

6. **Output Structure**
   - **Structured**: Mirror struktur `output_roi/`
   - **Flat**: Semua digit dalam 1 folder

**Output per TPS**: 12 files
- 9 individual digit images: `raw_<kode>_<tps>_<paslon>_pos1.jpg`
- 3 paslon row images: `raw_<kode>_<tps>_<paslon>.jpg`

> **Note**: Untuk fitur auto-cropping, install dengan: `pipenv install -e ".[extraction]"`

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
├── cli.py                          # Main CLI entry point (~130 lines)
├── setup.py                        # Package configuration with extras
├── Pipfile                         # Dependency management
├── Dockerfile                      # Core-only Docker image
├── Dockerfile.extraction           # Full-featured Docker image
├── docker-compose.yml              # Docker orchestration
├── DOCKER.md                       # Docker usage guide
│
├── cli_core/                       # 🆕 Modular CLI package (DI pattern)
│   ├── __init__.py                # Exports create_cli_injector
│   ├── injector.py                # CLI DI container
│   ├── config/
│   │   └── settings.py           # CLISettings dataclass
│   ├── context/                  # 🆕 Moved from root
│   │   └── tps.json             # Location and ID mappings
│   ├── utils/
│   │   ├── display.py           # Screen clearing, headers
│   │   └── data_provider.py     # LocationDataProvider
│   └── services/
│       ├── menu_service.py      # Interactive prompts (questionary)
│       ├── download_service.py  # Scrapy orchestration
│       ├── autocrop_service.py  # Extraction workflow
│       └── progress_service.py  # Progress tracking (tqdm)
│
├── kawal_pemilu_scraper/          # Scrapy spider
│   ├── spiders/
│   │   └── kawal_spider.py       # Main spider logic
│   ├── pipelines.py              # Image download pipeline
│   ├── settings.py               # Scrapy settings
│   └── middlewares.py            # Custom middlewares
│
├── jumlah_suara_extractor/        # Auto-cropping module (DI architecture)
│   ├── __init__.py               # Exports create_injector
│   ├── injector.py               # Extraction DI container
│   ├── core/                     # Business logic
│   │   ├── cropper.py           # DigitCropper with DI
│   │   ├── processors.py        # Border processing strategies
│   │   └── interfaces.py        # Abstract interfaces
│   ├── utils/                    # Utility functions
│   │   ├── naming.py            # Filename generation
│   │   ├── file_ops.py          # File operations
│   │   └── metrics.py           # Performance tracking
│   ├── services/                 # High-level services
│   │   ├── province_service.py  # Province detection
│   │   └── extraction_service.py # Extraction orchestration
│   ├── config/                   # Configuration
│   │   └── settings.py          # Settings dataclass
│   └── weights/                  # YOLOv11 model weights
│
├── output/                        # Regular C1 images
├── output_roi/                    # ROI images
├── output_digits/                 # 🆕 Extracted vote digits
└── README.md
```

### Modular Dependencies

The project uses `setup.py` with dependency groups:

**Core** (always installed):
- scrapy, questionary, tqdm, playwright

**Extraction** (optional):
- ultralytics, opencv-python, numpy, torch

**Dev** (optional):
- pytest, black, flake8, mypy

Install specific groups:
```bash
pipenv install -e ".[extraction]"  # Core + extraction
pipenv install -e ".[dev]"         # Core + dev tools
pipenv install --dev                # All features
```

### Key Components

**CLI Entry Point (`cli.py`)**: ~130 lines (78% reduction from 600+)
- Thin orchestration layer using dependency injection
- Workflow functions: `download_workflow()`, `autocrop_workflow()`
- Creates DI container and delegates to services

**CLI Core Services (`cli_core/services/`)**:
- **MenuService**: All interactive questionary prompts
- **DownloadService**: Scrapy subprocess orchestration
- **AutoCropService**: YOLO extraction workflow coordination
- **ProgressService**: tqdm progress bar wrapper

**Data Provider (`cli_core/utils/data_provider.py`)**:
- Lazy loading of location data from `cli_core/context/tps.json`
- Query methods: `get_provinces()`, `get_regencies()`, `get_districts()`

**Dependency Injection (`cli_core/injector.py`, `jumlah_suara_extractor/injector.py`)**:
- Factory methods for service creation
- Singleton pattern for shared resources
- Lazy loading of optional dependencies (ultralytics)

**Spider (`kawal_spider.py`)**:
- Async `start()` method (Scrapy 2.13+)
- Conditional extraction: regular vs ROI
- District name mapping from village IDs
- URL decoding for ROI images

**Scrapy Settings (`kawal_pemilu_scraper/settings.py`)**:
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
