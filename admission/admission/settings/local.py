import logging
from dotenv import load_dotenv, find_dotenv
from .base import *


if not load_dotenv(BASE_DIR.parent.joinpath(".env.local")):
    load_dotenv(find_dotenv(".env.local", raise_error_if_not_found=True))

logging.basicConfig(level=logging.INFO)
DEBUG = True

ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True

AUTH_PASSWORD_VALIDATORS = []

BOT_TOKEN = os.environ.get('BOT_TOKEN')

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = "6379"
REDIS_URL = (REDIS_HOST, REDIS_PORT)

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}

RQ_QUEUES = {
    'default': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DEFAULT_TIMEOUT': 360,
    },
}

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_NAME"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": 5432,
    }
}

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
