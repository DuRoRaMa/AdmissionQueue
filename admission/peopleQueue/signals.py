import django_rq

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from rq import Queue

from .max_tasks import send_talon_event_to_max
from .models import (
    OperatorLocation,
    TalonActions,
    TalonLog,
)
from .tasks import (
    send_to_tablo,
    send_to_tg_chat,
)


@receiver(post_save, sender=TalonLog)
async def on_talonlog_post_save(
    sender,
    instance: TalonLog,
    created: bool,
    raw: bool,
    using,
    update_fields,
    **kwargs,
):
    # Не обрабатываем повторное сохранение или загрузку фикстур.
    if not created or raw:
        return

    queue: Queue = django_rq.queues.get_queue()

    # Обновление информационного табло.
    queue.enqueue_in(
        timedelta(milliseconds=100),
        send_to_tablo,
        instance.pk,
    )

    # Уведомление пользователей MAX.
    # Этот блок должен находиться вне проверки tg_chat_id,
    # потому что MAX и Telegram являются независимыми каналами.
    if instance.action in {
        TalonActions.ASSIGNED,
        TalonActions.CANCELLED,
        TalonActions.COMPLETED,
    }:
        queue.enqueue(
            send_talon_event_to_max,
            instance.pk,
        )

    talon = instance.talon

    # Если Telegram к талону не привязан,
    # MAX-уведомление уже поставлено в очередь выше.
    if not talon.tg_chat_id:
        return

    minutes = 0
    text = ""

    if instance.action == TalonActions.CREATED:
        return

    if instance.action == TalonActions.ASSIGNED:
        created_by = await (
            get_user_model()
            .objects
            .select_related(
                "operator_settings",
                "operator_settings__location",
            )
            .aget(pk=instance.created_by_id)
        )

        operator_settings = created_by.operator_settings

        if operator_settings.location_id is None:
            return

        location = operator_settings.location

        text = (
            f"Статус талона {talon.name} обновлён!\n"
            f"Оператор ожидает вас за столом {location.name}"
        )

    elif instance.action == TalonActions.CANCELLED:
        text = (
            f"Статус талона {talon.name} обновлён!\n"
            "К сожалению, ваш талон больше недействителен.\n"
            "Чтобы взять новый талон, обратитесь, пожалуйста, "
            "на стойку ресепшена."
        )

    elif instance.action == TalonActions.COMPLETED:
        minutes = 5

        text = (
            f"Статус талона {talon.name} обновлён!\n"
            "Спасибо, что обратились в Приёмную комиссию ДВФУ.\n"
            'Свой отзыв вы можете оставить в меню «Мои талоны».'
        )

    else:
        # Для STARTED и REDIRECTED отдельное сообщение
        # сейчас не отправляется.
        return

    queue.enqueue_in(
        timedelta(minutes=minutes),
        send_to_tg_chat,
        talon.tg_chat_id,
        text,
    )