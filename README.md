
# 📸 Web Aplikasi Pemesanan Jasa Fotografi

WebApp ini adalah platform pemesanan jasa fotografi profesional berbasis web, dirancang khusus untuk mengelola layanan fotografi seperti wedding, pre-wedding.
Dikembangkan menggunakan **Python (Flask)**, aplikasi ini menyediakan sistem autentikasi peran, live chat, manajemen pemesanan, sistem pembayaran DP, invoice otomatis, dan kalender terintegrasi.

---

## 🚀 Fitur Utama

### ✅ Untuk Klien
- Registrasi dan login menggunakan email & nomor telepon
- Pemesanan layanan: wedding, pre-wedding, portrait, event
- Pemilihan paket wedding secara dinamis
- Upload bukti pembayaran DP
- Melihat status pesanan secara real-time
- Dashboard klien untuk:
  - Pesanan aktif
  - Riwayat pesanan
  - Download invoice PDF
- Live chat dengan admin
- Notifikasi (pesanan disetujui, ditolak, menunggu DP)
- Validasi otomatis: tidak bisa memesan untuk hari yang sama (H+0)

### 🛠️ Untuk Admin
- Dashboard statistik (klien, pesanan, pendapatan)
- Manajemen kalender otomatis (slot terisi dan dirilis)
- Menyetujui / menolak / membatalkan pesanan
- Validasi manual bukti transfer DP
- Kirim invoice ke email klien & tampilkan di dashboard
- Kelola paket wedding dan harga
- Export data transaksi (opsional)
- Respon chat klien

---

## 🧱 Teknologi yang Digunakan

| Komponen      | Teknologi                           |
|---------------|--------------------------------------|
| Backend       | Python, Flask, Flask-WTF, Jinja2, Celery, Redis |
| Auth          | Flask-Login, Flask-Bcrypt            |
| Database      | SQLite (dev), PostgreSQL (produksi)  |
| API & Logic   | REST-like endpoints                  |
| PDF Invoice   | WeasyPrint                           |
| Kalender      | JS Datepicker + backend validation   |
| Live Chat     | AJAX polling                         |
| Deployment    | Gunicorn + Nginx, Honcho (Local Dev) |

---

## 📂 Struktur Proyek

```
initialHGalelio/
├── app.py
├── config.py
├── models.py
├── forms.py
├── extensions.py
├── tasks.py
├── celery_worker_entrypoint.py
├── Procfile
├── /routes/
├── /templates/
├── /static/
├── /uploads/
└── requirements.txt
```

---

## 📦 Cara Menjalankan Aplikasi

### 1. Clone Repository
```bash
git clone https://github.com/initHD3v/initialHGalelio.git
cd initialHGalelio
```

### 2. Install Dependensi
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi (dengan Celery Worker)

Pastikan Redis server Anda berjalan di `localhost:6379`. Jika belum, instal dan jalankan:

```bash
# Untuk macOS dengan Homebrew
brew install redis
brew services start redis

# Untuk Linux dengan systemd
sudo apt update && sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

Kemudian, jalankan aplikasi Flask dan Celery worker secara bersamaan menggunakan `honcho`:

```bash
honcho start
```

Buka di browser: `http://127.0.0.1:5001`

---

## 💼 Alur Bisnis

1. Klien daftar & login
2. Melihat layanan & memilih tanggal
3. Order → status: `waiting_payment`
4. Upload bukti transfer DP → status: `waiting_approval`
5. Admin validasi DP → `accepted` → invoice dikirim
6. Jika ditolak → bisa upload ulang dalam waktu 1 jam
7. Setelah hari H → status: `done`, masuk riwayat
8. Slot dibatalkan → otomatis dirilis ke kalender

---

## 📸 Branding ArunaMoment

- Desain elegan & bersih
- Fokus pada storytelling visual
- Portofolio dapat di-like & dibagikan
- Responsif di semua perangkat

---

## 🔮 Rencana Pengembangan Selanjutnya

- [ ] REST API penuh untuk Flutter App
- [ ] Integrasi notifikasi WA otomatis
- [ ] WebSocket untuk chat live
- [ ] Multi-role admin (Staff, Superadmin)
- [ ] Laporan bulanan (PDF/Excel)


## 📃 Lisensi

© 2025 Aruna Moment. Semua hak cipta dilindungi.  
Aplikasi dikembangkan untuk kebutuhan internal dan komersial fotografi.

---

## 🗓️ Timeline Pengembangan (Juli 2025)

### Minggu 3 (20 Juli 2025)
- **Integrasi Celery untuk Tugas Latar Belakang Email:**
  - Mengimplementasikan Celery untuk pengiriman email asinkron (pendaftaran pengguna baru, notifikasi order, pembatalan, penjadwalan ulang).
  - Mengkonfigurasi Celery dengan Redis sebagai broker dan backend.
  - Merefaktor struktur aplikasi Flask ke pola factory function (`create_app`).
  - Menggunakan `honcho` untuk manajemen proses lokal (menjalankan Flask app dan Celery worker secara bersamaan).
  - Memperbaiki masalah konfigurasi SSL/TLS untuk pengiriman email.
  - Memastikan format email HTML yang dikirim sudah benar.
