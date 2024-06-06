from __future__ import annotations

import logging
import sys
from os import getenv

logger = logging.getLogger(__name__)
WEB_SERVER_HOST = "localhost"
WEB_SERVER_PORT = 8081
WEBHOOK_PATH = "/webhook"
# BASE_WEBHOOK_URL = getenv('BASE_URL', 'https://pavlyuk-it.ru')
BASE_WEBHOOK_URL = "https://8638-62-76-6-70.ngrok-free.app"
REDIS_URL = f"redis://{getenv('REDIS_HOST', 'localhost')}:6379"
TELEGRAM_API_TOKEN = getenv("BOT_TOKEN", default="")
if not TELEGRAM_API_TOKEN:
    logger.error("`TELEGRAM_API_TOKEN` is not set")
    sys.exit(1)
