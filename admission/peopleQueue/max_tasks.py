import logging

import requests
from django.conf import settings
from django_rq import job

from .models import TalonActions, TalonLog


logger = logging.getLogger(__name__)


@job
def send_talon_event_to_max(log_id: int) -> None:
    """Отправляет MAX-уведомления подписчикам талона."""

    try:
        log = (
            TalonLog.objects
            .select_related(
                "talon",
                "created_by",
                "created_by__operator_settings",
                "created_by__operator_settings__location",
            )
            .get(pk=log_id)
        )
    except TalonLog.DoesNotExist:
        logger.warning("TalonLog %s не найден", log_id)
        return

    if log.action not in {
        TalonActions.ASSIGNED,
        TalonActions.CANCELLED,
        TalonActions.COMPLETED,
    }:
        return

    subscriptions = (
        log.talon.messenger_subscriptions
        .filter(provider="max")
        .values_list("external_user_id", flat=True)
    )

    if log.action == TalonActions.ASSIGNED:
        event_type = "assigned"

        try:
            location = (
                log.created_by
                .operator_settings
                .location
            )
        except AttributeError:
            location = None
    elif log.action == TalonActions.CANCELLED:
        event_type = "cancelled"
        location = None
    else:
        event_type = "completed"
        location = None

    url = (
        settings.MAX_BOT_SERVICE_URL.rstrip("/")
        + "/internal/notifications/"
    )

    for external_user_id in subscriptions:
        payload = {
            "external_user_id": external_user_id,
            "type": event_type,
            "talon": {
                "id": log.talon_id,
                "name": log.talon.name,
            },
            "location": (
                location.name
                if location is not None
                else None
            ),
        }

        response = requests.post(
            url,
            json=payload,
            headers={
                "X-Internal-Token": (
                    settings.MAX_BOT_SERVICE_TOKEN
                )
            },
            timeout=10,
        )
        response.raise_for_status()
