from os import getenv

from aiogram import Bot
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from django_rq import job

from peopleQueue.models import OperatorSettings
from . import models


bot = Bot(getenv("BOT_TOKEN"))


@job
async def send_request_to_tg_chat(request_id: int):
    try:
        help_request = await models.HelpRequest.objects.select_related(
            "helper",
            "created_by",
            "theme",
        ).aget(pk=request_id)
    except models.HelpRequest.DoesNotExist:
        return

    helper = help_request.helper

    if helper is None or not helper.tg_chat_id:
        return

    created_by = help_request.created_by

    if created_by is None:
        from_by = "Неизвестный оператор"
        operator_settings = None
    else:
        from_by = created_by.get_full_name() or created_by.get_username()

        try:
            operator_settings = await OperatorSettings.objects.select_related(
                "location"
            ).aget(user=created_by)
        except OperatorSettings.DoesNotExist:
            operator_settings = None

    if operator_settings and operator_settings.location:
        from_by = f"{from_by} (Стол {operator_settings.location.name})"

    priority_emoji = {
        "Low": "",
        "Medium": "",
        "High": "",
    }

    priority = (
        help_request.get_priority_display()
        + priority_emoji.get(help_request.priority, "")
    )

    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Выполнить",
                    callback_data=f"helper:completed:{help_request.pk}",
                ),
            ]
        ]
    )

    text = (
        f"От: {from_by}\n"
        f"Срочность: {priority}\n"
        f"Тема: {help_request.theme}\n"
        f"Текст:\n{help_request.text}"
    )

    await bot.send_message(
        helper.tg_chat_id,
        text,
        reply_markup=reply_markup,
    )