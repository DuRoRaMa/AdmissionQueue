from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    '82.202.137.179',
    'localhost'
]
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = [
    'http://82.202.137.179',
]
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = [
    'http://82.202.137.179/',
]
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = True

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
