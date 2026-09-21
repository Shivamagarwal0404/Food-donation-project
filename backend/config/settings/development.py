"""
FoodShare — Development settings.
Overrides base settings for local development.
"""
import sys
from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ["*"]

USE_S3 = False

# For tests, use fast in-memory / SQLite database to avoid requiring PostgreSQL CREATEDB privileges
if "test" in sys.argv or any("pytest" in arg for arg in sys.argv) or config("USE_SQLITE", default=False, cast=bool):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test_db.sqlite3",
        }
    }

# Development CORS permissions: allow both localhost and 127.0.0.1 on Vite ports
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
CORS_ALLOW_ALL_ORIGINS = True
