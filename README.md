# Kawal Pemilu 2024 Scraper CLI

Aplikasi CLI interaktif untuk mengunduh gambar C1 Plano dari website KawalPemilu.org. Aplikasi ini memudahkan pengguna untuk mengunduh data secara massal berdasarkan wilayah (Provinsi, Kabupaten/Kota, Kecamatan).

## Fitur Utama
- **Menu Interaktif**: Navigasi mudah dengan keyboard (panah atas/bawah/enter).
- **Dua Mode Download**:
  - **Per Kecamatan**: Pilih spesifik kecamatan yang ingin diunduh.
  - **Satu Kabupaten (Bulk)**: Unduh seluruh desa di satu kabupaten sekaligus.
- **Progress Bar**: Tampilan status download real-time dengan estimasi waktu.
- **Struktur Folder Rapi**: Gambar tersimpan otomatis sesuai hierarki wilayah.
- **Teknologi**: Menggunakan Scrapy dan Playwright untuk menangani website dinamis.

## Prasyarat
- Python 3.10 atau lebih baru
- Pipenv (Manajer paket Python)

## Instalasi

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd kawal-pemilu-2024-scraper-cli
   ```

2. **Install Dependencies**
   Jalankan perintah berikut untuk menginstall semua library yang dibutuhkan:
   ```bash
   pipenv install
   ```

3. **Install Browser Playwright**
   Aplikasi membutuhkan browser Chromium untuk merender halaman web:
   ```bash
   pipenv run playwright install chromium
   ```

## Cara Penggunaan

1. **Jalankan Aplikasi**
   ```bash
   pipenv run python cli.py
   ```

2. **Ikuti Petunjuk di Layar**
   - Pilih **Mode Download** (Per Kecamatan atau Satu Kabupaten).
   - Pilih **Provinsi**.
   - Pilih **Kabupaten/Kota**.
   - (Jika mode Kecamatan) Pilih **Kecamatan**.
   - Pilih opsi **Verbose Logging** (Pilih 'Tidak' untuk tampilan bersih dengan progress bar).

3. **Tunggu Proses Selesai**
   Aplikasi akan menampilkan progress bar. Gambar yang berhasil diunduh akan tersimpan di folder `output`.

## Struktur Output
File gambar akan disimpan secara otomatis dengan struktur folder berikut:
```
output/
  └── NAMA PROVINSI/
      └── NAMA KABUPATEN/
          └── NAMA KECAMATAN/
              └── NAMA DESA/
                  └── raw_<kode_kelurahan>_<nomor_tps>_<hash>.jpg
```

Contoh nama file: `raw_1101012001_001_a1b2c.jpg`
- `1101012001`: Kode Kelurahan/Desa
- `001`: Nomor TPS (3 digit)
- `a1b2c`: Hash unik untuk membedakan halaman C1 (jika ada lebih dari 1 foto per TPS)


## Troubleshooting
- **Error: context/tps.json tidak ditemukan**: Pastikan file `tps.json` ada di dalam folder `context`.
- **Timeout**: Jika koneksi lambat, scraper mungkin mengalami timeout. Coba jalankan ulang dengan koneksi yang lebih stabil.
- **Verbose Mode**: Jika mengalami masalah, aktifkan mode "Ya (Tampilkan Log Lengkap)" untuk melihat detail error.

## Disclaimer
Aplikasi ini dibuat untuk tujuan edukasi dan pengumpulan data publik. Gunakan dengan bijak dan bertanggung jawab.
