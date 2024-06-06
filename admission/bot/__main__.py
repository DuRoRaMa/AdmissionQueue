import django
import os
if True:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                          'admission.settings.local')
    django.setup()
import logging
import sys

from aiogram import F, Bot, Dispatcher, Router
from aiogram.types import Message, BotCommand
from aiogram.types.bot_command_scope_default import BotCommandScopeDefault
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.filters import ExceptionTypeFilter
from aiogram_dialog import DialogManager, StartMode, setup_dialogs, ShowMode
from aiogram_dialog.api.exceptions import UnknownIntent, UnknownState
from aiohttp import web

from .config.bot import TELEGRAM_API_TOKEN, REDIS_URL, BASE_WEBHOOK_URL, WEB_SERVER_PORT, WEBHOOK_PATH
from .bot_dialogs import states
from .bot_dialogs.talon import talon_menu_dialog, talon_list_dialog
from .bot_dialogs.helper import callback_query, helper_dialog
from helper.models import Helper

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

dialog_router = Router()
dialog_router.include_routers(
    talon_menu_dialog,
    talon_list_dialog,
    helper_dialog
)


async def on_startup(bot: Bot) -> None:
    result = await bot.delete_webhook()
    print(f"Delete webhook result: {result}")
    result = await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}")
    print(f"Set webhook result: {result}")
    await bot.set_my_commands(commands=[
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/helper", description="Запустить помощника"),
    ], scope=BotCommandScopeDefault())


async def start(message: Message, dialog_manager: DialogManager):
    await dialog_manager.start(states.TalonMenu.GREETINGS, mode=StartMode.RESET_STACK)


async def start_helper(message: Message, dialog_manager: DialogManager):
    helper = await Helper.objects.filter(tg_chat_id=message.chat.id).acount()
    if helper == 0:
        await dialog_manager.start(states.TalonMenu.GREETINGS, mode=StartMode.RESET_STACK)
        return
    await dialog_manager.start(states.Helper.MAIN, mode=StartMode.RESET_STACK)


async def on_unknown_intent(event, dialog_manager: DialogManager):
    # Example of handling UnknownIntent Error and starting new dialog.
    logging.error("Restarting dialog: %s", event.exception)
    await dialog_manager.start(
        states.TalonMenu.GREETINGS, mode=StartMode.RESET_STACK, show_mode=ShowMode.SEND,
    )


async def on_unknown_state(event, dialog_manager: DialogManager):
    # Example of handling UnknownState Error and starting new dialog.
    logging.error("Restarting dialog: %s", event.exception)
    await dialog_manager.start(
        states.TalonMenu.GREETINGS, mode=StartMode.RESET_STACK, show_mode=ShowMode.SEND,
    )


def setup_dp():
    storage = RedisStorage.from_url(
        REDIS_URL,
        key_builder=DefaultKeyBuilder(with_destiny=True)
    )
    dp = Dispatcher(storage=storage)
    dp.startup.register(on_startup)
    dp.message.register(start, F.text == "/start")
    dp.message.register(start_helper, F.text == "/helper")
    dp.callback_query.register(*callback_query)
    dp.errors.register(
        on_unknown_intent,
        ExceptionTypeFilter(UnknownIntent),
    )
    dp.errors.register(
        on_unknown_state,
        ExceptionTypeFilter(UnknownState),
    )
    dp.include_router(dialog_router)
    setup_dialogs(dp)
    return dp


def main():
    app = web.Application()
    bot = Bot(TELEGRAM_API_TOKEN, parse_mode="HTML")
    dp = setup_dp()
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    logger.info('Starting webhook server')
    web.run_app(app, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    main()
