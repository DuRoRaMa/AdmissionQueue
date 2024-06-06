from os import getenv
from aiogram import Bot
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from django_rq import job
from . import models

bot = Bot(getenv("BOT_TOKEN"))


@job
async def send_request_to_tg_chat(request_id: int):
    request = await models.HelpRequest.objects.select_related('helper', 'created_by').aget(pk=request_id)
    helper = request.helper
    created_by = request.created_by
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Выполнить", callback_data=f"helper:completed:{request.pk}"),
            ]
        ]
    )
    text = f"От: {created_by.get_username()}\nСрочность: {
        request.get_priority_display()}\nТекст:\n{request.text}"
    await bot.send_message(
        helper.tg_chat_id,
        text,
        reply_markup=reply_markup
    )
