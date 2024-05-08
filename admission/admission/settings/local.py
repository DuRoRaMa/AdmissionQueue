from dotenv import load_dotenv
from .base import *

print(BASE_DIR.parent.joinpath(".env.local"))
if not load_dotenv(BASE_DIR.parent.joinpath(".env.local")):
    raise Exception("Failed to load .env")

DEBUG = True

ALLOWED_HOSTS = ['*']
# CORS_ALLOWED_ORIGINS = [
#     'http://localhost:5173',
#     'http://127.0.0.1:5173',
# ]
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
