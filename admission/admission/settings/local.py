import logging
from dotenv import load_dotenv
from .base import *

if not load_dotenv(BASE_DIR.parent.joinpath(".env.local")):
    raise Exception("Failed to load .env")

logging.basicConfig(level=logging.INFO)
DEBUG = True

ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

AUTH_PASSWORD_VALIDATORS = []

REDIS_HOST = os.environ.get('REDIS_HOST')
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_NAME"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST"),
        "PORT": 5432,
    }
}

SERVER_DOMAIN = "https://f413-62-76-6-70.ngrok-free.app"
