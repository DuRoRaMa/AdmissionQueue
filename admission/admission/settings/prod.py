from dotenv import load_dotenv
from .base import *
if os.environ.get('CI'):
    if not load_dotenv(os.environ.get('.env.production')):
        raise Exception("Failed to load CI .env")
else:
    if not load_dotenv(BASE_DIR.parent.joinpath(".env.production")):
        raise Exception("Failed to load .env")

DEBUG = False

ALLOWED_HOSTS = ['95.174.92.61']
CORS_ALLOWED_ORIGINS = [
    'http://95.172.92.61'
]

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

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
