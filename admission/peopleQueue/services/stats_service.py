from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timedelta
from typing import Any

from django.db.models import Prefetch
from django.utils import timezone

from ..models import Talon, TalonActions, TalonLog


STATUS_LABELS = dict(TalonActions.choices)


def _parse_datetime_param(value: str | None, *, is_end: bool = False) -> datetime:
    """
    Поддерживает форматы:
    - 2026-06-03
    - 2026-06-03T10:00:00
    - 2026-06-03T10:00:00+10:00

    Если end передан как дата без времени, то считаем весь день:
    end=2026-06-03 -> 2026-06-04 00:00:00
    """
    current_tz = timezone.get_current_timezone()

    if not value:
        now = timezone.localtime()

        if is_end:
            return now

        return timezone.make_aware(
            datetime.combine(now.date(), time.min),
            current_tz,
        )

    date_only = len(value) == 10

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed, current_tz)

    if is_end and date_only:
        parsed = parsed + timedelta(days=1)

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


def _first_log(logs: list[TalonLog], actions: set[str]) -> TalonLog | None:
    for log in logs:
        if log.action in actions:
            return log

    return None


def _increment_status(bucket: dict[str, Any], status: str) -> None:
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
    elif status == TalonActions.REDIRECTED:
        bucket["redirected"] += 1


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
            "total": 0,
            "completed": 0,
            "cancelled": 0,
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
        hour_key = f"{local_created_at.hour:02d}:00"

        by_day[day_key]["date"] = day_key
        by_day[day_key]["total"] += 1
        _increment_status(by_day[day_key], status)

        by_hour[hour_key]["hour"] = hour_key
        by_hour[hour_key]["total"] += 1

        if status == TalonActions.COMPLETED:
            by_hour[hour_key]["completed"] += 1
        elif status == TalonActions.CANCELLED:
            by_hour[hour_key]["cancelled"] += 1

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
            user = log.created_by

            if not user:
                continue

            if user.pk not in by_operator:
                by_operator[user.pk] = {
                    "id": user.pk,
                    "username": user.username,
                    "assigned": 0,
                    "started": 0,
                    "completed": 0,
                    "cancelled": 0,
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
                    by_operator[user.pk]["_service_seconds"].append(service)

            elif log.action == TalonActions.CANCELLED:
                by_operator[user.pk]["cancelled"] += 1

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
