from os import getenv
from aiogram import Bot
from django_rq import job
from channels.layers import get_channel_layer
from .models import Talon

bot = Bot(getenv("BOT_TOKEN", ""))
channel_layer = get_channel_layer()


@job
async def send_to_tablo(id: int) -> None:
    await channel_layer.group_send('tablo', {"type": 'talonLog.create', 'message': id})

@job
async def send_to_admin(text: str, talon: Talon) -> None:
    # type: ignore
    last_log = await talon.logs.select_related('created_by').alast()
    await bot.send_message(649116862, f"{last_log} - {text}")


@job
async def send_to_tg_chat(chat_id: int, text: str) -> None:
    await bot.send_message(chat_id, text)
