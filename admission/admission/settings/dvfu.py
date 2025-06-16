from .base import *

DEBUG = False
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
# Разрешенные хосты
ALLOWED_HOSTS = [
    'vinogradov-it.ru',      # Основной домен
    'www.vinogradov-it.ru',  # WWW поддомен
   
    'localhost',
    'backend',               # Имя сервиса в Docker
    'aq-backend',            # Имя контейнера
]

# Настройки CORS
CORS_ORIGIN_ALLOW_ALL = False
CORS_ALLOWED_ORIGINS = [
    'https://vinogradov-it.ru',
    'https://www.vinogradov-it.ru',
]

# Важно для работы за прокси (Nginx)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Доверенные источники для CSRF
CSRF_TRUSTED_ORIGINS = [
    'https://vinogradov-it.ru',
    'https://www.vinogradov-it.ru'
]

# Безопасные куки (включить для HTTPS)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True  # Рекомендуется для безопасности

# Настройки домена кук
CSRF_COOKIE_DOMAIN = 'vinogradov-it.ru'  # Точка в начале для поддоменов
SESSION_COOKIE_DOMAIN = 'vinogradov-it.ru'

# Валидаторы паролей
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

# Настройки бота
BOT_TOKEN = os.environ.get('BOT_TOKEN')
BASE_URL = 'https://vinogradov-it.ru'  # Важно обновить!

# Настройки Redis
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')  # Имя сервиса в Docker
REDIS_PORT = "6379"
REDIS_URL = (REDIS_HOST, REDIS_PORT)

# Каналы
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [f"redis://{REDIS_HOST}:{REDIS_PORT}/0"],
            "symmetric_encryption_keys": [SECRET_KEY],
        },
    },
}

# Очереди
RQ_QUEUES = {
    'default': {
        'HOST': REDIS_HOST,
        'PORT': REDIS_PORT,
        'DB': 0,
        'DEFAULT_TIMEOUT': 360,
        'SSL': False,
    },
}

# Настройки базы данных
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_NAME"),
        "USER": os.environ.get("POSTGRES_USER"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD"),
        "HOST": os.environ.get("POSTGRES_HOST", "pgdb"),  # Имя сервиса в Docker
        "PORT": 5432,
        "CONN_MAX_AGE": 600,  # Подключения с пуллом
    }
}

# Секретный ключ
# Добавьте в существующий settings.py

# WebSocket настройки
WEBSOCKET_URL = '/graphql/'
WEBSOCKET_KEEPALIVE = 25  # Интервал ping-пакетов в секундах
FERNET_KEY = os.environ.get('FERNET_KEY')

# Настройки Channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(os.environ.get('REDIS_HOST', 'redis'), 6379)],
            "symmetric_encryption_keys": [SECRET_KEY],
            "channel_capacity": {
                "http.request": 1000,
                "websocket.receive": 1000,
            },
            "connection_kwargs": {
                "health_check_interval": 30,
                "socket_keepalive": True,
            },
        },
    },
}

# Логирование WebSocket
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'websocket': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/websocket.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'loggers': {
        'websocket': {
            'handlers': ['websocket'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Дополнительные настройки безопасности
SECURE_HSTS_SECONDS = 31536000  # 1 год
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Настройки статических файлов
STATIC_URL = '/static/'
STATIC_ROOT = '/app/static'  # Путь для сбора статики

# Настройки медиа файлов
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'
