from . import states
from aiogram.types import CallbackQuery, Message, Chat
from aiogram_dialog import Dialog, DialogManager, Window, SubManager
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Start, Row, Button, SwitchTo, Back, Next, ScrollingGroup, ListGroup
from peopleQueue.models import Talon, TalonLog


async def on_talon_comment_input(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    comment = message.text
    dialog_manager.dialog_data['comment'] = comment
    await dialog_manager.next()
    talon = await Talon.objects.aget(pk=dialog_manager.dialog_data.get('id'))
    talon.comment = comment
    await talon.asave()


async def on_talon_id_input(message: Message, widget: MessageInput, dialog_manager: DialogManager):
    try:
        talon = await Talon.objects.aget(id=int(message.text))
    except Talon.DoesNotExist:
        await dialog_manager.switch_to(states.TalonMenu.TALON_NOT_FOUND)
        return
    except ValueError:
        await dialog_manager.switch_to(states.TalonMenu.TALON_NOT_FOUND)
        return
    if talon.tg_chat_id:
        if talon.tg_chat_id != message.chat.id:
            await dialog_manager.switch_to(states.TalonMenu.TALON_IS_BUSY)
            return
    talon.tg_chat_id = message.chat.id
    await talon.asave()
    dialog_manager.dialog_data['talon_name'] = talon.name
    await dialog_manager.switch_to(states.TalonMenu.SUBSCRIBED)


async def sub_getter(dialog_manager: DialogManager, **kwargs):
    return {'talon_name': dialog_manager.dialog_data.get('talon_name')}


async def list_getter(event_chat: Chat, **kwargs):
    talons = Talon.objects.order_by(
        '-created_at').filter(tg_chat_id=event_chat.id)
    data = {'talons': []}
    async for talon in talons:
        last_action = await talon.aget_last_action()
        status = ""
        if last_action == TalonLog.Actions.COMPLETED:
            status = 'Завершен'
        elif last_action == TalonLog.Actions.CANCELLED:
            status = 'Отменен'
        elif last_action == TalonLog.Actions.ASSIGNED:
            status = 'Оператор ожидает Вас'
        elif last_action == TalonLog.Actions.STARTED:
            status = 'В процессе'
        elif last_action == TalonLog.Actions.CREATED:
            status = 'В ожидании'
        elif last_action == TalonLog.Actions.REDIRECTED:
            status = 'В ожидании'
        data['talons'].append({
            'id': talon.id,
            'name': talon.name,
            'status': status
        })
    return data


async def info_getter(dialog_manager: DialogManager, **kwargs):
    return dialog_manager.dialog_data


async def to_info_window(callback: CallbackQuery, button: Button, manager: SubManager, **kwargs):
    talon_id = int(manager.item_id)
    talon = await Talon.objects.aget(id=talon_id)
    manager.dialog_data['id'] = talon.id
    manager.dialog_data['name'] = talon.name
    manager.dialog_data['created_at'] = talon.created_at.astimezone().strftime(
        '%d.%m.%Y %H:%M')
    last_action = await talon.aget_last_action()
    if last_action == TalonLog.Actions.COMPLETED:
        status = 'Завершен'
    elif last_action == TalonLog.Actions.CANCELLED:
        status = 'Отменен'
    elif last_action == TalonLog.Actions.ASSIGNED:
        status = 'Оператор ожидает Вас'
    elif last_action == TalonLog.Actions.STARTED:
        status = 'В процессе'
    elif last_action == TalonLog.Actions.CREATED:
        status = 'В ожидании'
    elif last_action == TalonLog.Actions.REDIRECTED:
        status = 'В ожидании'
    manager.dialog_data['is_commented'] = talon.comment is not None
    manager.dialog_data['is_not_commented'] = talon.comment is None
    manager.dialog_data['comment'] = talon.comment
    manager.dialog_data['status'] = status

    await manager.switch_to(button.state)


START_MAIN_MENU = Start(
    Const("Меню"),
    id="go_talon_menu",
    state=states.TalonMenu.GREETINGS
)


talon_menu_dialog = Dialog(
    Window(
        Const(
            'Привет!\nЭто бот электронной очереди Приемной комиссии ДВФУ!\nДля того чтобы узнавать о новых событиях талона нажмите на "Подписаться"'
        ),
        Row(
            Start(Const("Мои талоны"), id="my_talons",
                  state=states.Talon.LIST),
            Next(Const("Подписаться"), id="try_to_subscribe"),
        ),
        state=states.TalonMenu.GREETINGS
    ),
    Window(
        Format("Напишите код на талоне, чтобы подписаться на его обновления"),
        Back(Const('Назад')),
        MessageInput(on_talon_id_input),
        state=states.TalonMenu.SUBSCRIBING,
    ),
    Window(
        Format("Вы подписались на обновления талона <b>{talon_name}</b>"),
        SwitchTo(
            Const("Меню"),
            id='go_main_after_sub',
            state=states.TalonMenu.GREETINGS
        ),
        state=states.TalonMenu.SUBSCRIBED,
        getter=sub_getter,
    ),
    Window(
        Const("Талон с таким номером не найден"),
        SwitchTo(
            Const("Назад"),
            id='go_main_after_sub',
            state=states.TalonMenu.SUBSCRIBING
        ),
        state=states.TalonMenu.TALON_NOT_FOUND,
    ),
    Window(
        Const("Данный талон уже кем-то занят"),
        SwitchTo(
            Const("Назад"),
            id='go_main_after_sub',
            state=states.TalonMenu.SUBSCRIBING
        ),
        state=states.TalonMenu.TALON_IS_BUSY,
    ),
)

talon_list_dialog = Dialog(
    Window(
        Const('Список Ваших талонов:'),
        ScrollingGroup(
            ListGroup(
                SwitchTo(
                    text=Format(
                        "{item[name]} - {item[status]}"
                    ),
                    on_click=to_info_window,
                    id='talon_list_item',
                    state=states.Talon.INFO
                ),
                id='talon_list_LG',
                item_id_getter=lambda item: item['id'],
                items='talons',
            ),
            id='talon_list_SG',
            height=3,
            hide_on_single_page=True
        ),
        START_MAIN_MENU,
        state=states.Talon.LIST,
        getter=list_getter
    ),
    Window(
        Format(
            "Номер талона: {name}\nДата создания: {created_at}\nСтатус: {status}"
        ),
        Next(Const('Оставить отзыв'), when='is_not_commented'),
        SwitchTo(Const('Мой отзыв'), id="talon_is_commented",
                 state=states.Talon.COMMENTED, when='is_commented'),
        Row(
            START_MAIN_MENU,
            Back(Const('Назад')),
        ),
        state=states.Talon.INFO,
        getter=info_getter
    ),
    Window(
        Format(
            "Напишите свой отзыв к талону {name} {created_at}"
        ),
        MessageInput(on_talon_comment_input),
        Row(
            START_MAIN_MENU,
            Back(Const('Назад')),
        ),
        state=states.Talon.COMMENT,
        getter=info_getter
    ),
    Window(
        Format(
            "{comment}\n\nСпасибо за Ваш отзыв!"
        ),
        START_MAIN_MENU,
        state=states.Talon.COMMENTED,
        getter=info_getter
    ),
)
