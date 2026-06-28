import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()


def _build_db_uri():
    """Mendukung 2 cara koneksi database:
    1) TIDB_DATABASE_URL / DATABASE_URL langsung.
    2) Variabel terpisah DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME.
    """
    direct_uri = os.getenv("TIDB_DATABASE_URL") or os.getenv("DATABASE_URL")
    if direct_uri:
        return direct_uri

    db_host = os.getenv("DB_HOST")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME")
    db_port = os.getenv("DB_PORT", "4000")

    if all([db_host, db_user, db_password, db_name]):
        user = quote_plus(db_user)
        password = quote_plus(db_password)
        ssl_query = ""
        # TiDB Cloud public endpoint umumnya butuh TLS/SSL.
        if os.getenv("DB_SSL", "true").lower() in {"1", "true", "yes", "on"}:
            ssl_query = "?ssl_verify_cert=true&ssl_verify_identity=true"
        return f"mysql+pymysql://{user}:{password}@{db_host}:{db_port}/{db_name}{ssl_query}"

    # Fallback agar project tetap bisa dijalankan di Vercel dan lingkungan readonly.
    if os.getenv("VERCEL", "").lower() in {"1", "true", "yes"} or os.path.exists("/tmp"):
        return "sqlite:////tmp/portfolio_local.db"
    return "sqlite:///portfolio_local.db"


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-this")

    SQLALCHEMY_DATABASE_URI = _build_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
    }

    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    CONTACT_RECEIVER_EMAIL = os.getenv("CONTACT_RECEIVER_EMAIL") or os.getenv("ADMIN_EMAIL")
    CONTACT_SENDER_EMAIL = os.getenv("CONTACT_SENDER_EMAIL", "Portfolio <onboarding@resend.dev>")
