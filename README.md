# Portfolio PA Flask - Deploy Ready

Project ini sudah disiapkan untuk tugas portofolio dinamis berbasis Flask dengan integrasi TiDB Cloud, Cloudinary, Resend, dan Vercel.

## Yang sudah disiapkan

- Flask app dengan entrypoint `app.py` dan variabel `app` agar bisa dibaca Vercel.
- Database dinamis menggunakan SQLAlchemy.
- Mendukung TiDB melalui `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, atau `TIDB_DATABASE_URL`.
- Upload gambar profil/proyek ke Cloudinary.
- Form kontak menyimpan pesan ke database dan mengirim email via Resend jika API key tersedia.
- Admin login dan CRUD profil, skill, pengalaman, proyek, kontak.
- `.env.example` dan `vercel-env-template.txt`.
- SQL root project: `DB_682024076_Matumadeta.sql`.
- `vercel.json` untuk routing Flask di Vercel.

## Jalankan lokal

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python app.py
```

Buka:

```text
http://127.0.0.1:5000
```

Admin:

```text
http://127.0.0.1:5000/admin/login
```

Default:

```text
Username: admin
Password: admin123
```

## Deploy

Ikuti `CHECKLIST_DEPLOY.md`.

## Link Vercel dan Routes

Setelah deploy, buka:

- Website utama: `https://<your-vercel-domain>/`
- Admin login: `https://<your-vercel-domain>/admin/login`

Ganti `<your-vercel-domain>` dengan domain yang diberikan Vercel setelah import dan deploy.

## Penting

Jangan upload `.env` asli ke GitHub atau ZIP pengumpulan. Gunakan `.env.example` saja.
