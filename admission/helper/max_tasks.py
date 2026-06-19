import logging

import requests
from django.conf import settings
from django_rq import job

from peopleQueue.models import OperatorSettings
from . import models


logger = logging.getLogger(__name__)


def build_created_by_text(help_request: models.HelpRequest) -> str:
    created_by = help_request.created_by

    if created_by is None:
        return "Неизвестный оператор"

    from_by = created_by.get_full_name() or created_by.get_username()

    try:
        operator_settings = OperatorSettings.objects.select_related(
            "location"
        ).get(user=created_by)
    except OperatorSettings.DoesNotExist:
        return from_by

    if operator_settings.location:
        return f"{from_by} (Стол {operator_settings.location.name})"

    return from_by


@job
def send_request_to_max(request_id: int) -> None:
    try:
        help_request = (
            models.HelpRequest.objects.select_related(
                "helper",
                "theme",
                "created_by",
            )
            .get(pk=request_id)
        )
    except models.HelpRequest.DoesNotExist:
        logger.warning("HelpRequest %s не найден", request_id)
        return

    helper = help_request.helper

    if helper is None:
        logger.info(
            "HelpRequest %s не отправлен в MAX: helper отсутствует",
            request_id,
        )
        return

    if not helper.max_user_id:
        logger.info(
            "HelpRequest %s не отправлен в MAX: у helper %s нет max_user_id",
            request_id,
            helper.pk,
        )
        return

    service_url = getattr(settings, "MAX_BOT_SERVICE_URL", "")
    service_token = getattr(settings, "MAX_BOT_SERVICE_TOKEN", "")

    if not service_url or not service_token:
        logger.warning(
            "MAX_BOT_SERVICE_URL или MAX_BOT_SERVICE_TOKEN не настроены"
        )
        return

    url = service_url.rstrip("/") + "/internal/notifications/"

    payload = {
        "external_user_id": helper.max_user_id,
        "type": "helper_request",
        "helper_request": {
            "id": help_request.pk,
            "from": build_created_by_text(help_request),
            "priority": help_request.get_priority_display(),
            "theme": str(help_request.theme),
            "text": help_request.text,
            "created_at": help_request.created_at.astimezone().strftime(
                "%d.%m.%Y %H:%M"
            ),
        },
    }

    response = requests.post(
        url,
        json=payload,
        headers={
            "X-Internal-Token": service_token,
        },
        timeout=10,
    )
    response.raise_for_status()