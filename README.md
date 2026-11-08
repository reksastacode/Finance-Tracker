# Keuangan Mandiri - Personal Finance Tracker 

Aplikasi desktop manajemen dan pelacakan keuangan pribadi berbasis **Python 3.13** dan **PySide6** (Qt for Python) dengan arsitektur **MVVM (Model-View-ViewModel)** dan persistensi basis data lokal **SQLite 3**.

> 📖 **Dokumentasi Lengkap & Arsitektur Teknis**: Silakan baca berkas [DOKUMENTASI_PROYEK.md](file:///c:/Users/meiza/projectPemVis/DOKUMENTASI_PROYEK.md) untuk penjelasan mendalam mengenai arsitektur, skema basis data, konkurensi multi-threading, dan linimasa pengembangan dari Pertemuan 1 hingga Pertemuan 10.

---

## 🎨 Palet Warna & Desain Antarmuka
Aplikasi mengusung tema estetis *Sage Pastel* yang ramah di mata:
- **Sidebar**: `#A8BFA3` (Sage green)
- **Background Utama**: `#F7F5F0` (Soft warm white)
- **Card Background**: `#FFFFFF` (Pure white)
- **Tombol Utama**: `#7F9B7A` (Forest sage green)
- **Aksen Pemasukan**: `#7FAE8A` (Green)
- **Aksen Pengeluaran**: `#C98787` (Coral red)
- **Aksen Target/Tabungan**: `#A99ABF` (Lavender)

---

## ✨ Modul & Fitur Utama

1. **Dashboard Analitik**:
   - Ringkasan KPI reaktif: Saldo Saat Ini, Total Pemasukan, Total Pengeluaran, Total Target.
   - Grafik tren keuangan multi-dataset (`QPainter`, filter periode: Minggu ini, Bulan ini, Tahun ini).
   - Kalender transaksi bulanan interaktif dengan tag chip harian (-Rp80k, +Rp100k, $Rp790k).
   - Pratinjau cepat aktivitas terbaru dan target aktif.
2. **Input Transaksi (Operasi CRUD Form)**:
   - Form pencatatan pemasukan & pengeluaran.
   - Auto-formatting mata uang `Rp` secara instan saat mengetik (`textChanged`).
   - Dynamic category loading berdasarkan jenis transaksi.
   - Live character counter `0/100` pada kolom keterangan.
   - Animated Toast notification feedback.
3. **Kategori (Operasi CRUD Grid)**:
   - Tab switching reaktif: *Kategori Pengeluaran* vs *Kategori Pemasukan*.
   - Grid kartu kategori dengan aksi Tambah, Ubah (Edit), dan Hapus (Delete).
   - Audit trail tooltip pada setiap kartu kategori.
4. **Riwayat Transaksi (Operasi CRUD Table)**:
   - Multi-criteria filter: Pencarian teks, jenis transaksi, kategori, dan rentang tanggal.
   - Pagination virtual (50 transaksi/halaman) yang ditenagai oleh background worker `QThread`.
   - Perhitungan otomatis kolom *Saldo Setelah* per transaksi secara kronologis.
   - Fitur Ekspor Riwayat ke format CSV.
   - Audit trail tooltip pada setiap sel tabel (ID, created_at, updated_at).
5. **Target Keuangan (Tabungan Berorientasi Target)**:
   - Pelacakan akumulasi tabungan, kebutuhan sisa, dan persentase pencapaian.
   - Kartu target dengan visualisasi progress bar dan badge prioritas (*Tinggi*, *Sedang*, *Rendah*).
    - Modal **Isi Target / Nabung**: Mengalokasikan dana langsung dari saldo dengan transaksi atomik.

6. **File System & Local Storage**:
   - Semua berkas lokal tersentralisasi di folder `data/`: SQLite, konfigurasi, cache, lampiran, ekspor, backup, dan kunci.
   - Catatan sensitif, cache, backup, serta lampiran dienkripsi; Windows memakai DPAPI untuk melindungi kunci tanpa password tambahan.
   - Lampiran struk mendukung PNG/JPG/WEBP/GIF/BMP/PDF/TXT dengan batas ukuran yang dapat diatur.
   - Dialog **Pengaturan** mengelola cache, pagination, periode grafik, batas lampiran, enkripsi, backup, dan restore.

---

## 💾 Persistensi Data (SQLite 3 - Pertemuan 10)
Aplikasi menggunakan database relasional SQLite 3 (`data/keuangan_mandiri.db`) dengan:
- **Mode WAL (Write-Ahead Logging)** untuk konkurensi baca/tulis tanpa blokir.
- **SQL Triggers** untuk audit trail waktu otomatis (`created_at`, `updated_at`).
- **Indeks Performa** pada kolom tanggal, jenis, dan kategori.
- **Self-Healing**: Pembuatan skema tabel otomatis jika berkas database dihapus manual.
- **Data versioning**: Trigger perubahan data membatalkan cache turunan secara otomatis.
- **Backup terenkripsi**: Snapshot SQLite konsisten dan lampiran dibungkus dalam arsip `.kmbak`.
- **Storage paths**: Semua file aplikasi berada di bawah `data/`.

---

## 🚀 Panduan Menjalankan Aplikasi & Utilitas

### 1. Menjalankan Aplikasi Desktop:
```powershell
py -3.13 main.py
```

### 2. Menginspeksi Isi Database Langsung di Terminal:
```powershell
py -3.13 tools/inspect_database.py
```

### 3. Mengelola & Mereset Database:
* **Reset ke kondisi kosong** (untuk input data mandiri):
  ```powershell
  py -3.13 tools/reset_database.py --clean
  ```
* **Restore data demo 2.000 transaksi** (untuk presentasi):
  ```powershell
  py -3.13 tools/reset_database.py --demo
  ```

### 4. Menjalankan Pengujian Unit (Unit Tests):
```powershell
py -3.13 -m unittest discover -s tests
```
*(30/30 tests passed, termasuk storage, encryption, backup, attachment, dan offscreen UI smoke test)*
