import logging

import django_rq
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from rq import Queue
from datetime import timedelta
from .max_tasks import send_talon_event_to_max
from .models import TalonActions, TalonLog
from .tasks import send_to_tablo, send_to_tg_chat


logger = logging.getLogger(__name__)


@receiver(post_save, sender=TalonLog)
def on_talonlog_post_save(
    sender,
    instance: TalonLog,
    created: bool,
    raw: bool,
    using,
    update_fields,
    **kwargs,
):
    if not created or raw:
        return

    logger.warning(
        "TalonLog signal fired: id=%s action=%s talon=%s",
        instance.pk,
        instance.action,
        instance.talon_id,
    )

    queue: Queue = django_rq.get_queue("default")

    # Обновление информационного табло.
    queue.enqueue_in(
        timedelta(milliseconds=100),
        send_to_tablo,
        instance.pk,
    )

    # MAX-уведомления. Важно: этот блок НЕ зависит от tg_chat_id.
    if instance.action in {
        TalonActions.ASSIGNED,
        TalonActions.CANCELLED,
        TalonActions.COMPLETED,
    }:
        logger.warning(
            "Enqueue MAX notification: log_id=%s action=%s",
            instance.pk,
            instance.action,
        )

        queue.enqueue(
            send_talon_event_to_max,
            instance.pk,
        )

    talon = instance.talon

    # Telegram-уведомления остаются отдельно.
    if not talon.tg_chat_id:
        return

    minutes = 0
    text = ""

    if instance.action == TalonActions.CREATED:
        return

    if instance.action == TalonActions.ASSIGNED:
        created_by = (
            get_user_model()
            .objects
            .select_related(
                "operator_settings",
                "operator_settings__location",
            )
            .get(pk=instance.created_by_id)
        )

        try:
            operator_settings = created_by.operator_settings
        except created_by.__class__.operator_settings.RelatedObjectDoesNotExist:
            return

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
            "Свой отзыв вы можете оставить в меню «Мои талоны»."
        )

    else:
        return

    queue.enqueue_in(
        timedelta(minutes=minutes),
        send_to_tg_chat,
        talon.tg_chat_id,
        text,
    )
