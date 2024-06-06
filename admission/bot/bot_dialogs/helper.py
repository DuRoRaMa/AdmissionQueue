from . import states
from aiogram import F
from aiogram.types import CallbackQuery, Message, Chat
from aiogram.types.inline_keyboard_markup import InlineKeyboardMarkup
from aiogram.types.inline_keyboard_button import InlineKeyboardButton
from aiogram.filters.callback_data import CallbackData
from aiogram_dialog import Dialog, DialogManager, Window, SubManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Start, Row, Button, SwitchTo, Back, Next, ScrollingGroup, ListGroup
from helper.models import HelpRequest, Helper


class CompletedRequestCD(CallbackData, prefix="helper"):
    action: str
    request_id: str


async def on_completed_request(query: CallbackQuery, callback_data: CompletedRequestCD):
    await query.message.edit_reply_markup()
    await query.message.edit_text(f"{query.message.text}\n\nВЫПОЛНЕНО!")
    request = await HelpRequest.objects.aget(pk=int(callback_data.request_id))
    request.completed = True
    await request.asave()


callback_query = (on_completed_request, CompletedRequestCD.filter(
    F.action == "completed"
))


async def info_getter(event_chat: Chat, dialog_manager: DialogManager, **kwargs):
    helper = await Helper.objects.select_related('user').aget(tg_chat_id=event_chat.id)
    data = {
        'is_active': helper.is_active,
        'is_not_active': not helper.is_active,
        'sector': helper.sector,
        'username': helper.user.get_username(),
        'count': await HelpRequest.objects.filter(completed=False, helper=helper.id).acount(),
    }
    dialog_manager.dialog_data.update(data)
    return data


async def on_set_invert_active(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    is_active = dialog_manager.dialog_data['is_active']
    helper = await Helper.objects.aget(tg_chat_id=callback.message.chat.id)
    helper.is_active = not is_active
    await helper.asave()
    dialog_manager.dialog_data['is_active'] = not is_active
    dialog_manager.dialog_data['is_not_active'] = is_active
    await callback.answer()


async def on_repeat_active_requests(callback: CallbackQuery, button: Button, dialog_manager: DialogManager):
    helper = await Helper.objects.aget(tg_chat_id=callback.message.chat.id)
    async for request in HelpRequest.objects.select_related('created_by').filter(completed=False, helper=helper.id):
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
        await callback.bot.send_message(
            helper.tg_chat_id,
            text,
            reply_markup=reply_markup
        )
    await callback.answer()

helper_dialog = Dialog(
    Window(
        Format("Привет {username}!"),
        Format("Зона ответственности: {sector}"),
        Button(
            Const('Активен'),
            on_click=on_set_invert_active,
            id="Active",
            when='is_active',
        ),
        Button(
            Const('Не активен'),
            on_click=on_set_invert_active,
            id="Not_Active",
            when='is_not_active',
        ),
        Button(
            Format('Повторить активные запросы: {count}'),
            on_click=on_repeat_active_requests,
            id="Repeat_Requests",
        ),
        state=states.Helper.MAIN,
    ),
    getter=info_getter,
)
