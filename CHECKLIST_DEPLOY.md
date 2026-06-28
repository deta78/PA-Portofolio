# Checklist Deploy Portfolio PA

## 1. TiDB Cloud
1. Buat resource TiDB Cloud Starter.
2. Buka SQL Editor.
3. Jalankan:

```sql
CREATE DATABASE IF NOT EXISTS portfolio_db;
USE portfolio_db;
```

4. Copy isi `DB_682024076_Matumadeta.sql`, paste ke SQL Editor, lalu Run.
5. Ambil data koneksi: host, port, username, password.

## 2. Cloudinary
1. Buka Dashboard Cloudinary > API Keys.
2. Ambil Cloud Name, API Key, API Secret.
3. Isi ke `.env` lokal dan Environment Variables di Vercel.

## 3. Resend
1. Buat API key di Resend.
2. Isi `RESEND_API_KEY`.
3. Untuk akun gratis, gunakan `CONTACT_SENDER_EMAIL=Portfolio <onboarding@resend.dev>` dan kirim ke email akun Resend kamu.

## 4. Vercel
1. Upload/push folder project ini ke GitHub.
2. Import project di Vercel.
3. Buka Project Settings > Environment Variables.
4. Klik Import `.env`, lalu paste isi dari `vercel-env-template.txt` yang sudah kamu ganti value-nya.
5. Pilih Production, Preview, Development jika tersedia.
6. Save, lalu Redeploy.

## 5. Tes
- Website utama: `https://<your-vercel-domain>/`
- Login admin: `https://<your-vercel-domain>/admin/login`
- Routes lokal:
  - Main: `/`
  - Admin: `/admin/login`
- Default admin: `admin` / `admin123`, kecuali sudah diganti di Environment Variables.
- Upload gambar dari halaman admin profil/proyek, cek Media Library Cloudinary.
- Kirim pesan dari form kontak, cek dashboard Resend dan email penerima.

## Catatan keamanan
Jangan commit file `.env`. Jika password/API key pernah terlihat di screenshot/chat, rotate/ganti secret setelah deploy berhasil.
