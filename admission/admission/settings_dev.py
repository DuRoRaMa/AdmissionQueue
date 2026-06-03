import logging
import os

from dotenv import find_dotenv, load_dotenv

from .settings.base import *


# Загружаем локальные переменные окружения.
# Файл .env.local должен лежать в корне репозитория AdmissionQueue,
# то есть рядом с requirements.txt.
ENV_FILE = BASE_DIR.parent / ".env.local"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    load_dotenv(find_dotenv(".env.local", usecwd=True))


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.lower() in ("1", "true", "yes", "y", "on")


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)

    return [item.strip() for item in value.split(",") if item.strip()]


logging.basicConfig(level=logging.INFO)


# =========================
# Основные настройки Django
# =========================

DEBUG = True

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "dev-only-secret-key-change-me",
)

ALLOWED_HOSTS = "localhost,127.0.0.1,0.0.0.0".split(',')

AUTH_PASSWORD_VALIDATORS = []


# =========================
# CORS / CSRF для фронта
# =========================

CORS_ALLOW_ALL_ORIGINS = False

CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)

CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)

CORS_ALLOW_CREDENTIALS = True


# =========================
# База данных
# =========================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_NAME", "bd"),
        "USER": os.getenv("POSTGRES_USER", "user"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "secret_pass"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": int(os.getenv("POSTGRES_PORT", "5432")),
    }
}


# =========================
# Redis / Channels / RQ
# =========================

USE_REDIS = env_bool("USE_REDIS", False)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

if USE_REDIS:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [(REDIS_HOST, REDIS_PORT)],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels.layers.InMemoryChannelLayer",
        },
    }

RQ_QUEUES = {
    "default": {
        "HOST": REDIS_HOST,
        "PORT": REDIS_PORT,
        "DB": REDIS_DB,
        "DEFAULT_TIMEOUT": 360,
    },
}


# =========================
# Боты / внешние ссылки
# =========================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


# =========================
# Почта в dev
# =========================

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# =========================
# Статика / медиа
# =========================

STATIC_URL = "/static/"
MEDIA_URL = "/media/"