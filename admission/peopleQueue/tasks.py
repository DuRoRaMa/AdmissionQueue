from os import getenv
from aiogram import Bot
from django_rq import job
from .models import Talon, TalonLog

bot = Bot(getenv("BOT_TOKEN"))


@job
async def send_to_admin(text: str, talon: Talon) -> None:
    last_log = await talon.logs.select_related('created_by').alast()
    await bot.send_message(649116862, f"{last_log} - {text}")


@job
async def send_to_tg_chat(chat_id: int, text: str) -> None:
    await bot.send_message(chat_id, text)
