# Keuangan Mandiri - Personal Finance Tracker 

Aplikasi desktop tracking keuangan berbasis **Python** dan **PySide6** dengan arsitektur **MVVM (Model-View-ViewModel)**.

---

## Palet Warna & Desain UI
- **Sidebar**: `#A8BFA3` (Sage green)
- **Background**: `#F7F5F0` (Soft warm white)
- **Card**: `#FFFFFF` (Pure white)
- **Tombol Utama**: `#7F9B7A` (Forest sage green)
- **Pemasukan**: `#7FAE8A` (Green)
- **Pengeluaran**: `#C98787` (Coral red)
- **Target**: `#A99ABF` (Lavender)

---

## Modul & Fitur (Fase 1 - 4)

1. **Dashboard Keuangan**:
   - Ringkasan KPI Saldo Saat Ini, Total Pemasukan, Total Pengeluaran, Total Target.
   - Grafik Keuangan garis multi-dataset interaktif (`paintEvent`, filter periode: Minggu ini, Bulan ini, Tahun ini).
   - Kalender Transaksi bulanan dengan penanda/tag chip harian (-Rp80k, +Rp100k, $Rp790k).
   - Preview Target Keuangan aktif dan Transaksi Terbaru.
2. **Input Transaksi**:
   - Form pencatatan pemasukan & pengeluaran.
   - Auto-formatting mata uang `Rp` secara real-time (`textChanged` event).
   - Dynamic category loading berdasarkan jenis transaksi.
   - Live character counter `0/100` pada kolom keterangan.
   - Animated Toast notification ("Transaksi berhasil disimpan!" & "Transaksi dibatalkan").
3. **Kategori**:
   - Tab switching reaktif: *Kategori Pengeluaran* vs *Kategori Pemasukan*.
   - Grid kartu kategori dengan aksi Ubah (Edit) dan Hapus (Delete).
   - Modal dialog Tambah & Edit Kategori.
4. **Riwayat Transaksi**:
   - Ringkasan statistik transaksi terfilter.
   - Multi-criteria filter bar: Jenis Transaksi, Kategori, Tanggal Mulai, dan Tanggal Akhir.
   - Tabel interaktif dengan perhitungan otomatis *Saldo Setelah* per baris transaksi.
5. **Target Keuangan**:
   - Ringkasan metrik total target, dana dibutuhkan, dana terkumpul, dan persentase progres.
   - Kartu target dengan badge prioritas (*Tinggi*, *Sedang*, *Rendah*) dan progress bar.
   - Modal **Isi Target**: Alokasi tabungan langsung dari saldo tersedia dengan validasi live.
   - Tips Menabung dan riwayat aktivitas alokasi terbaru.
     
---

##  Cara Menjalankan Aplikasi

### 1. Menjalankan Aplikasi Desktop:
```bash
python main.py
```
