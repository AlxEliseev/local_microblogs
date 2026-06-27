import os
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent

MEDIA_STORAGE = Path(os.getenv("MEDIA_STORAGE", APP_DIR / "media"))

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://admin:admin@postgres:5432/twitter_db"
)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")