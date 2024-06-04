# from __future__ import annotations
# import os
# from typing import TYPE_CHECKING
# from functools import wraps

# from aiogram import Router, Bot
# from aiogram.filters import Command, CommandObject
# from aiogram.fsm.state import State, StatesGroup
# from aiogram_dialog import Dialog, DialogManager, StartMode, Window
# import django


# if TYPE_CHECKING:
#     from aiogram.types import Message

# router = Router()


# class TalonSG(StatesGroup):
#     greetings = State()
#     show_talon_list = State()
#     talon_feedback = State()
#     current_talon = State()
#     subscribe_talon = State()
#     unsubscribe_talon = State()
#     talon_not_found = State()
#     talon_is_busy = State()


# def standalone(function):
#     @wraps(function)
#     def _wrapper(*args, **kwargs):
#         os.environ.setdefault('DJANGO_SETTINGS_MODULE',
#                               'admission.settings.local')
#         django.setup()
#         return function(*args, **kwargs)
#     return _wrapper


# @router.message(Command(commands=["start"]))
# @standalone
# async def handle_start_command(message: Message, bot: Bot, command: CommandObject) -> None:
#     if command.args:
#         from peopleQueue.models import Talon
#         try:
#             talon = await Talon.objects.aget(pk=int(command.args))
#         except Talon.DoesNotExist:
#             await message.answer(f"Талона с таким кодом не существует")
#             return
#         if talon.tg_chat_id is not None:
#             await message.answer(f"На талон уже кто-то подписан. К сожалению, вы не можете на него подписаться")
#             return
#         talon.tg_chat_id = message.chat.id
#         await talon.asave()
#         await message.answer(f"Вы подписались на обновления событий талона {talon.name}")
#     else:
#         await message.answer("Это бот электронной очереди приемной комиссии ДВФУ!\nНапишите особый номер на талоне, чтобы подписаться на его обновления.")
#
#
# @router.message(Command(commands=["id"]))
# async def handle_id_command(message: Message) -> None:
#     if message.from_user is None:
#         return

#     await message.answer(
#         f"User Id: <b>{
#             message.from_user.id}</b>\nChat Id: <b>{message.chat.id}</b>",
#     )


# @router.message(Command("start"))
# async def handle_start_command(message: Message, dialog_manager: DialogManager) -> None:
#     # Important: always set `mode=StartMode.RESET_STACK` you don't want to stack dialogs
#     await dialog_manager.start(TalonSG.talon_quiz, mode=StartMode.RESET_STACK)


# main_window = Window(
#     Const("Hello, unknown person"),  # just a constant text
#     Button(Const("Useless button"), id="nothing"),  # button with text and id
#     state=TalonSG.talon_quiz,  # state is used to identify window between dialogs
# )

# dialog = Dialog(main_window)
