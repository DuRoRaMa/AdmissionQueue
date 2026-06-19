import logging

import requests
from django.conf import settings
from django_rq import job

from peopleQueue.models import OperatorSettings
from . import models

logger = logging.getLogger(__name__)


def get_operator_title(user) -> str:
    if user is None:
        return "Неизвестно"

    name = user.get_full_name() or user.get_username() or str(user)
    operator_settings = (
        OperatorSettings.objects
        .select_related("location")
        .filter(user=user)
        .first()
    )

    if operator_settings and operator_settings.location:
        return f"{name} (Стол {operator_settings.location.name})"

    return name


@job
def send_request_to_max(request_id: int) -> None:
    try:
        help_request = (
            models.HelpRequest.objects
            .select_related("helper", "created_by", "theme")
            .get(pk=request_id)
        )
    except models.HelpRequest.DoesNotExist:
        logger.warning("HelpRequest %s не найден", request_id)
        return

    helper = help_request.helper
    if helper is None:
        logger.info("HelpRequest %s не имеет помощника", request_id)
        return

    if not helper.max_user_id:
        logger.info(
            "У помощника %s не указан max_user_id, MAX-уведомление не отправлено",
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

    payload = {
        "external_user_id": str(helper.max_user_id),
        "type": "helper_request",
        "helper_request": {
            "id": help_request.pk,
            "from": get_operator_title(help_request.created_by),
            "theme": str(help_request.theme),
            "priority": help_request.get_priority_display(),
            "text": help_request.text or "",
            "created_at": help_request.created_at.astimezone().strftime(
                "%d.%m.%Y %H:%M"
            ),
        },
    }

    url = service_url.rstrip("/") + "/internal/notifications/"

    try:
        response = requests.post(
            url,
            json=payload,
            headers={"X-Internal-Token": service_token},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        logger.exception(
            "Не удалось отправить MAX-уведомление по HelpRequest %s",
            request_id,
        )
        raise