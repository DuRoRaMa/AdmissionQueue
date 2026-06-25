from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta
from typing import Any

from django.db.models import Prefetch
from django.utils import timezone

from ..models import Talon, TalonActions, TalonLog
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError

STATUS_LABELS = dict(TalonActions.choices)


def _parse_datetime_param(value, is_end=False):
    if not value:
        return None

    value = str(value).strip()

    parsed = None
    is_date_only = False

    # 1. Пробуем ISO: 2026-06-26 или 2026-06-26T10:30:00
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

        # Если пришла только дата без времени
        if "T" not in value and " " not in value:
            is_date_only = True

    except ValueError:
        # 2. Пробуем русский формат: 26.06.2026
        try:
            parsed_date = datetime.strptime(value, "%d.%m.%Y").date()
            parsed = datetime.combine(
                parsed_date,
                time.max if is_end else time.min,
            )
            is_date_only = True

        except ValueError:
            raise ValidationError(
                {
                    "date": (
                        "Некорректный формат даты. "
                        "Используйте YYYY-MM-DD или DD.MM.YYYY."
                    )
                }
            )

    # Если ISO был только датой, для end ставим конец дня
    if is_date_only and is_end:
        parsed = datetime.combine(parsed.date(), time.max)

    if is_date_only and not is_end:
        parsed = datetime.combine(parsed.date(), time.min)

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, timezone.get_current_timezone())

    return parsed


def _seconds_between(start: datetime | None, end: datetime | None) -> int | None:
    if not start or not end:
        return None

    seconds = int((end - start).total_seconds())

    if seconds < 0:
        return None

    return seconds


def _avg(values: list[int]) -> int:
    if not values:
        return 0

    return int(sum(values) / len(values))

def _operator_service_period(
    operator_logs: list[TalonLog],
) -> tuple[datetime | None, datetime | None]:
    """
    Определяет период работы конкретного оператора с талоном.

    Начало:
    первый STARTED.

    Окончание:
    первый COMPLETED, CANCELLED или REDIRECTED после начала.
    """

    started_at: datetime | None = None

    for log in operator_logs:
        if (
            started_at is None
            and log.action == TalonActions.STARTED
        ):
            started_at = log.created_at
            continue

        if (
            started_at is not None
            and log.action
            in {
                TalonActions.COMPLETED,
                TalonActions.CANCELLED,
                TalonActions.REDIRECTED,
            }
        ):
            return started_at, log.created_at

    return started_at, None

def _first_log(logs: list[TalonLog], actions: set[str]) -> TalonLog | None:
    for log in logs:
        if log.action in actions:
            return log

    return None


def _increment_status(
    bucket: dict[str, Any],
    status: str,
) -> None:
    """
    Увеличивает количество талонов по их текущему состоянию.

    REDIRECTED здесь не учитывается, потому что переадресация является
    событием журнала, а не стабильным итоговым состоянием талона.
    """

    if status == TalonActions.CREATED:
        bucket["waiting"] += 1
    elif status == TalonActions.ASSIGNED:
        bucket["assigned"] += 1
    elif status == TalonActions.STARTED:
        bucket["started"] += 1
    elif status == TalonActions.COMPLETED:
        bucket["completed"] += 1
    elif status == TalonActions.CANCELLED:
        bucket["cancelled"] += 1


def get_queue_statistics(params: dict[str, Any]) -> dict[str, Any]:
    start = _parse_datetime_param(params.get("start"), is_end=False)
    end = _parse_datetime_param(params.get("end"), is_end=True)

    purpose_id = params.get("purpose")
    operator_id = params.get("operator")
    status_value = params.get("status")

    logs_queryset = (
        TalonLog.objects
        .select_related("created_by")
        .order_by("created_at")
    )

    talons_queryset = (
        Talon.objects
        .select_related("purpose", "updated_by")
        .prefetch_related(Prefetch("logs", queryset=logs_queryset))
        .filter(created_at__gte=start, created_at__lt=end)
        .order_by("created_at")
    )

    if purpose_id:
        talons_queryset = talons_queryset.filter(purpose_id=purpose_id)

    if status_value:
        talons_queryset = talons_queryset.filter(action=status_value)

    if operator_id:
        talons_queryset = talons_queryset.filter(
            logs__created_by_id=operator_id
        ).distinct()

    talons = list(talons_queryset)

    summary = {
        "total": len(talons),
        "waiting": 0,
        "assigned": 0,
        "started": 0,
        "in_service": 0,
        "completed": 0,
        "cancelled": 0,
        "redirected": 0,
        "avg_wait_seconds": 0,
        "avg_service_seconds": 0,
    }

    by_day: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "date": "",
            "total": 0,
            "waiting": 0,
            "assigned": 0,
            "started": 0,
            "completed": 0,
            "cancelled": 0,
            "redirected": 0,
        }
    )

    by_hour: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "hour": "",
            "created": 0,
            "completed": 0,
            "cancelled": 0,
            "redirected": 0,
        }
    )

    by_purpose: dict[int, dict[str, Any]] = {}

    by_operator: dict[int, dict[str, Any]] = {}

    wait_seconds: list[int] = []
    service_seconds: list[int] = []

    for talon in talons:
        status = talon.action

        _increment_status(summary, status)

        if status in (TalonActions.ASSIGNED, TalonActions.STARTED) and talon.compliting:
            summary["in_service"] += 1

        local_created_at = timezone.localtime(talon.created_at)
        day_key = local_created_at.date().isoformat()
        created_hour_key = f"{local_created_at.hour:02d}:00"

        by_day[day_key]["date"] = day_key
        by_day[day_key]["total"] += 1
        _increment_status(by_day[day_key], status)

        by_hour[created_hour_key]["hour"] = created_hour_key
        by_hour[created_hour_key]["created"] += 1

        if status == TalonActions.COMPLETED:
            by_hour[created_hour_key]["completed"] += 1
        elif status == TalonActions.CANCELLED:
            by_hour[created_hour_key]["cancelled"] += 1

        purpose = talon.purpose

        if purpose.pk not in by_purpose:
            by_purpose[purpose.pk] = {
                "id": purpose.pk,
                "name": purpose.name,
                "code": purpose.code,
                "total": 0,
                "waiting": 0,
                "assigned": 0,
                "started": 0,
                "completed": 0,
                "cancelled": 0,
                "redirected": 0,
            }

        by_purpose[purpose.pk]["total"] += 1
        _increment_status(by_purpose[purpose.pk], status)

        logs = list(talon.logs.all())
        redirect_logs = [
            log
            for log in logs
            if log.action == TalonActions.REDIRECTED
        ]

        redirect_count = len(redirect_logs)

        summary["redirected"] += redirect_count
        by_day[day_key]["redirected"] += redirect_count
        by_purpose[purpose.pk]["redirected"] += redirect_count
        assigned_log = _first_log(
            logs,
            {TalonActions.ASSIGNED, TalonActions.STARTED},
        )
        started_log = _first_log(logs, {TalonActions.STARTED})
        completed_log = _first_log(logs, {TalonActions.COMPLETED})

        wait = _seconds_between(
            talon.created_at,
            assigned_log.created_at if assigned_log else None,
        )

        if wait is not None:
            wait_seconds.append(wait)

        service = _seconds_between(
            started_log.created_at if started_log else None,
            completed_log.created_at if completed_log else None,
        )

        if service is not None:
            service_seconds.append(service)

        for log in logs:
            local_log_created_at = timezone.localtime(
                log.created_at
            )

            log_hour_key = (
                f"{local_log_created_at.hour:02d}:00"
            )

            by_hour[log_hour_key]["hour"] = log_hour_key

            if log.action == TalonActions.COMPLETED:
                by_hour[log_hour_key]["completed"] += 1

            elif log.action == TalonActions.CANCELLED:
                by_hour[log_hour_key]["cancelled"] += 1

            elif log.action == TalonActions.REDIRECTED:
                by_hour[log_hour_key]["redirected"] += 1

            user = log.created_by

            if not user:
                continue

            if user.pk not in by_operator:
                by_operator[user.pk] = {
                    "id": user.pk,
                    "username": user.username,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "full_name": user.get_full_name(),
                    "assigned": 0,
                    "started": 0,
                    "completed": 0,
                    "cancelled": 0,
                    "redirected": 0,
                    "notified": 0,
                    "avg_service_seconds": 0,
                    "_service_seconds": [],
                }

            if log.action == TalonActions.ASSIGNED:
                by_operator[user.pk]["assigned"] += 1

            elif log.action == TalonActions.STARTED:
                by_operator[user.pk]["started"] += 1

            elif log.action == TalonActions.COMPLETED:
                by_operator[user.pk]["completed"] += 1

                if service is not None:
                    by_operator[user.pk][
                        "_service_seconds"
                    ].append(service)

            elif log.action == TalonActions.CANCELLED:
                by_operator[user.pk]["cancelled"] += 1

            elif log.action == TalonActions.REDIRECTED:
                by_operator[user.pk]["redirected"] += 1
            summary["avg_wait_seconds"] = _avg(wait_seconds)
            summary["avg_service_seconds"] = _avg(service_seconds)

    operators_result = []

    for item in by_operator.values():
        item["avg_service_seconds"] = _avg(item["_service_seconds"])
        item.pop("_service_seconds", None)
        operators_result.append(item)

    return {
        "filters": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "purpose": purpose_id,
            "operator": operator_id,
            "status": status_value,
        },
        "summary": summary,
        "by_day": sorted(by_day.values(), key=lambda item: item["date"]),
        "by_hour": sorted(by_hour.values(), key=lambda item: item["hour"]),
        "by_purpose": sorted(
            by_purpose.values(),
            key=lambda item: item["id"],
        ),
        "by_operator": sorted(
            operators_result,
            key=lambda item: item["completed"],
            reverse=True,
        ),
        "status_labels": STATUS_LABELS,
    }




def _format_user(user) -> dict[str, Any] | None:
    if not user:
        return None

    return {
        "id": user.pk,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.get_full_name(),
    }


def _log_to_dict(log: TalonLog) -> dict[str, Any]:
    return {
        "id": log.pk,
        "action": log.action,
        "action_label": STATUS_LABELS.get(log.action, log.action),
        "comment": log.comment,
        "created_at": timezone.localtime(log.created_at).isoformat(),
        "created_by": _format_user(log.created_by),
    }


def get_operator_detailed_statistics(
    operator_id: int,
    params: dict[str, Any],
) -> dict[str, Any]:
    operator_id = int(operator_id)

    User = get_user_model()

    operator = User.objects.get(pk=operator_id)

    start = _parse_datetime_param(params.get("start"), is_end=False)
    end = _parse_datetime_param(params.get("end"), is_end=True)

    purpose_id = params.get("purpose")
    status_value = params.get("status")

    logs_queryset = (
        TalonLog.objects
        .select_related("created_by")
        .order_by("created_at")
    )

    talons_queryset = (
        Talon.objects
        .select_related("purpose", "updated_by")
        .prefetch_related(Prefetch("logs", queryset=logs_queryset))
        .filter(
            logs__created_by_id=operator_id,
            created_at__gte=start,
            created_at__lt=end,
        )
        .distinct()
        .order_by("-created_at")
    )

    if purpose_id:
        talons_queryset = talons_queryset.filter(purpose_id=purpose_id)

    if status_value:
        talons_queryset = talons_queryset.filter(action=status_value)

    talons = list(talons_queryset)

    summary = {
        "total": len(talons),
        "assigned": 0,
        "started": 0,
        "completed": 0,
        "cancelled": 0,
        "redirected": 0,
        "notified": 0,
        "avg_wait_seconds": 0,
        "avg_service_seconds": 0,
    }

    wait_seconds_values: list[int] = []
    service_seconds_values: list[int] = []

    talons_result: list[dict[str, Any]] = []

    for talon in talons:
        logs = list(talon.logs.all())

        operator_logs = [
            log for log in logs
            if log.created_by_id == operator_id
        ]

        assigned_log = _first_log(
            operator_logs,
            {TalonActions.ASSIGNED, TalonActions.STARTED},
        )
        started_log = _first_log(operator_logs, {TalonActions.STARTED})
        completed_log = _first_log(operator_logs, {TalonActions.COMPLETED})
        cancelled_log = _first_log(operator_logs, {TalonActions.CANCELLED})

        for log in operator_logs:
            if log.action == TalonActions.ASSIGNED:
                summary["assigned"] += 1
            elif log.action == TalonActions.STARTED:
                summary["started"] += 1
            elif log.action == TalonActions.COMPLETED:
                summary["completed"] += 1
            elif log.action == TalonActions.CANCELLED:
                summary["cancelled"] += 1
            elif log.action == TalonActions.REDIRECTED:
                summary["redirected"] += 1

        wait_seconds = _seconds_between(
            talon.created_at,
            assigned_log.created_at if assigned_log else None,
        )

        service_started_at, service_finished_at = (
            _operator_service_period(operator_logs)
        )

        service_seconds = _seconds_between(
            service_started_at,
            service_finished_at,
        )

        if wait_seconds is not None:
            wait_seconds_values.append(wait_seconds)

        if service_seconds is not None:
            service_seconds_values.append(service_seconds)

        talons_result.append(
            {
                "id": talon.pk,
                "name": talon.name,
                "ordinal": talon.ordinal,
                "status": talon.action,
                "status_label": STATUS_LABELS.get(talon.action, talon.action),
                "purpose": {
                    "id": talon.purpose_id,
                    "name": talon.purpose.name,
                    "code": talon.purpose.code,
                },
                "created_at": timezone.localtime(talon.created_at).isoformat(),
                "assigned_at": (
                    timezone.localtime(assigned_log.created_at).isoformat()
                    if assigned_log else None
                ),
                "started_at": (
                    timezone.localtime(started_log.created_at).isoformat()
                    if started_log else None
                ),
                "completed_at": (
                    timezone.localtime(completed_log.created_at).isoformat()
                    if completed_log else None
                ),
                "cancelled_at": (
                    timezone.localtime(cancelled_log.created_at).isoformat()
                    if cancelled_log else None
                ),
                "wait_seconds": wait_seconds,
                "service_seconds": service_seconds,
                "comment": talon.comment,
                "logs": [_log_to_dict(log) for log in logs],
                "operator_logs": [_log_to_dict(log) for log in operator_logs],
            }
        )

    summary["avg_wait_seconds"] = _avg(wait_seconds_values)
    summary["avg_service_seconds"] = _avg(service_seconds_values)

    return {
        "filters": {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "purpose": purpose_id,
            "status": status_value,
        },
        "operator": _format_user(operator),
        "summary": summary,
        "talons": talons_result,
        "status_labels": STATUS_LABELS,
    }

def get_queue_statistics_filters() -> dict[str, Any]:
    User = get_user_model()

    purposes = (
        Talon.objects
        .select_related("purpose")
        .values(
            "purpose_id",
            "purpose__name",
            "purpose__code",
        )
        .distinct()
        .order_by("purpose__name")
    )

    operators = (
        User.objects
        .filter(talon_logs__isnull=False)
        .distinct()
        .order_by("last_name", "first_name", "username")
    )

    return {
        "purposes": [
            {
                "id": item["purpose_id"],
                "name": item["purpose__name"],
                "code": item["purpose__code"],
            }
            for item in purposes
            if item["purpose_id"] is not None
        ],
        "operators": [
            {
                "id": operator.pk,
                "username": operator.username,
                "first_name": operator.first_name,
                "last_name": operator.last_name,
                "full_name": operator.get_full_name(),
            }
            for operator in operators
        ],
        "statuses": STATUS_LABELS,
    }