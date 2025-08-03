# Server Management Panel

Aplikasi web untuk manajemen server yang dibuat dengan Python Flask dan TailwindCSS. Aplikasi ini dapat memonitor:
- Penggunaan CPU, Memory, dan Disk
- Status layanan Nginx, PHP-FPM, dan MySQL
- Informasi MySQL

## Persyaratan Sistem

- Python 3.8 atau lebih tinggi
- Nginx
- PHP-FPM
- MySQL/MariaDB
- pip (Python package manager)

## Instalasi

1. Clone repository ini:
```bash
git clone https://github.com/basoro/slemp.git
cd slemp
```

2. Buat virtual environment Python:
```bash
python -m venv venv
source venv/bin/activate 
```

3. Install dependensi yang diperlukan:
```bash
pip install -r requirements.txt
```

4. Jalankan aplikasi:
```bash
python app.py
```

5. Buka browser dan akses:
```
http://localhost:5000
```

Username: admin
Password: admin

## Fitur

1. Monitor Sistem:
   - Penggunaan CPU real-time
   - Penggunaan Memory real-time
   - Penggunaan Disk real-time

2. Monitor Layanan:
   - Status Nginx
   - Status PHP-FPM
   - Status MySQL

3. Informasi MySQL:
   - Versi MySQL
   - Jumlah koneksi aktif

## Pengembangan

Aplikasi ini menggunakan:
- Flask sebagai web framework
- SQLAlchemy untuk ORM
- TailwindCSS untuk UI
- Chart.js untuk visualisasi data

## Keamanan

Pastikan untuk:
1. Menggunakan kredensial yang aman untuk akses MySQL
2. Membatasi akses ke aplikasi menggunakan firewall
3. Menggunakan HTTPS jika diakses dari jaringan publik

## Lisensi

MIT License Copyright (c) 2023 Basoro