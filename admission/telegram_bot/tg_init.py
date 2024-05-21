from django.conf import settings
from telegram import Bot
from telegram.ext import Dispatcher

from handlers import conv_handler


def telegram_bot():
    bot = Bot(settings.BOT_TOKEN)
    return bot


def telegram_dispatcher():
    bot = telegram_bot()
    dispatcher = Dispatcher(bot, None, workers=0)

    # Register handlers here
    dispatcher.add_handler(conv_handler)

    return dispatcher


BOT = telegram_bot()
DISPATCHER = telegram_dispatcher()
