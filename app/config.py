import os

from dotenv import load_dotenv

load_dotenv()


def _get_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    return int(value) if value is not None else default


APP_ENV = _get_str("APP_ENV", "local").lower()
API_HOST = _get_str("API_HOST", "0.0.0.0")
API_PORT = _get_int("API_PORT", 8000)
PUBLIC_API_BASE_URL = _get_str("PUBLIC_API_BASE_URL", f"http://localhost:{API_PORT}").rstrip("/")

DATABASE_URL = _get_str(
    "DATABASE_URL",
    "mysql+pymysql://root:your_mysql_password@localhost/rideshare_db",
)

SECRET_KEY = _get_str("SECRET_KEY", "your-secret-key-keep-it-secret")
ALGORITHM = _get_str("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = _get_int("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
REFRESH_TOKEN_EXPIRE_DAYS = _get_int("REFRESH_TOKEN_EXPIRE_DAYS", 7)

SMTP_SERVER = _get_str("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = _get_int("SMTP_PORT", 587)
SMTP_USER = _get_str("SMTP_USER")
SMTP_PASSWORD = _get_str("SMTP_PASSWORD")
SENDER_EMAIL = _get_str("SENDER_EMAIL", SMTP_USER)
RESEND_API_KEY = _get_str("RESEND_API_KEY")
EMAIL_PROVIDER = _get_str("EMAIL_PROVIDER", "auto").lower()
