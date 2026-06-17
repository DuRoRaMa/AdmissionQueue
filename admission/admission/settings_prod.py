import os
from .settings.base import *


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "y", "on")


def env_list(name: str, default: str = "") -> list[str]:
    value = os.getenv(name, default)
    return [item.strip() for item in value.split(",") if item.strip()]


# ============================================================
# Основные настройки production
# ============================================================

DEBUG = False

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY is required in production")

ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    "pk-services.dvfu.ru,localhost,127.0.0.1",
)

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ============================================================
# Работа за внешним nginx / reverse proxy
# ============================================================

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Внешний nginx уже принимает HTTPS, поэтому внутри контейнера редирект лучше
# не включать, пока точно не проверена схема проксирования.
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"


# ============================================================
# Запуск backend не из корня домена, а из /queue-backend/
# ============================================================

FORCE_SCRIPT_NAME = os.getenv("DJANGO_FORCE_SCRIPT_NAME", "").rstrip("/") or None

if FORCE_SCRIPT_NAME:
    STATIC_URL = f"{FORCE_SCRIPT_NAME}/static/"
    MEDIA_URL = f"{FORCE_SCRIPT_NAME}/media/"
else:
    STATIC_URL = "/static/"
    MEDIA_URL = "/media/"

STATIC_ROOT = BASE_DIR / "static"
MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# CORS / CSRF
# ============================================================

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = env_list(
    "CORS_ALLOWED_ORIGINS",
    "https://pk-services.dvfu.ru",
)
CSRF_TRUSTED_ORIGINS = env_list(
    "CSRF_TRUSTED_ORIGINS",
    "https://pk-services.dvfu.ru",
)
CORS_ALLOW_CREDENTIALS = True


# ============================================================
# PostgreSQL
# ============================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_NAME", "admission_queue"),
        "USER": os.getenv("POSTGRES_USER", "admission_queue"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST", "postgres"),
        "PORT": int(os.getenv("POSTGRES_PORT", "5432")),
        "CONN_MAX_AGE": int(os.getenv("POSTGRES_CONN_MAX_AGE", "60")),
    }
}

if not DATABASES["default"]["PASSWORD"]:
    raise RuntimeError("POSTGRES_PASSWORD is required in production")


# ============================================================
# Redis / Channels / RQ
# ============================================================

USE_REDIS = True

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
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


# ============================================================
# Telegram / MAX bot
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")

MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
MAX_BOT_INTERNAL_TOKEN = os.getenv("MAX_BOT_INTERNAL_TOKEN", "")
MAX_BOT_SERVICE_URL = os.getenv("MAX_BOT_SERVICE_URL", "http://max-bot:3000")
MAX_BOT_SERVICE_TOKEN = os.getenv("MAX_BOT_SERVICE_TOKEN", "")

if not MAX_BOT_INTERNAL_TOKEN:
    raise RuntimeError("MAX_BOT_INTERNAL_TOKEN is required in production")

if not MAX_BOT_SERVICE_TOKEN:
    raise RuntimeError("MAX_BOT_SERVICE_TOKEN is required in production")


# ============================================================
# Внешние ссылки
# ============================================================

BASE_URL = os.getenv("BASE_URL", "https://pk-services.dvfu.ru/queue-backend")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://pk-services.dvfu.ru/queue")


# ============================================================
# Email
# ============================================================

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)


# ============================================================
# DRF
# ============================================================

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [
    "rest_framework.renderers.JSONRenderer",
]


# ============================================================
# Логирование
# ============================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
    },
}