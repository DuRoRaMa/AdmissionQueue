from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from peopleQueue.models import (
    OperatorQueue,
    OperatorSettings,
    Talon,
    TalonActions,
)


OPERATOR_IDLE_TIMEOUT_MINUTES = 60


def release_inactive_operator_locations() -> int:
    """
    Освобождает рабочее место оператора, если:

    1. у оператора выбран стол;
    2. у оператора нет активного талона;
    3. последняя активность оператора была более часа назад.

    Активностью считаются:
    - последнее действие с талоном;
    - сохранение или изменение настроек оператора.

    Благодаря учёту OperatorSettings.updated_at только что выбранный
    стол не будет сразу освобождён при отсутствии журналов талонов.
    """

    now = timezone.now()
    cutoff = now - timedelta(
        minutes=OPERATOR_IDLE_TIMEOUT_MINUTES
    )

    released_count = 0

    settings_queryset = (
        OperatorSettings.objects
        .select_related("user", "location")
        .filter(location__isnull=False)
    )

    for operator_settings in settings_queryset:
        user = operator_settings.user

        has_active_talon = Talon.objects.filter(
            updated_by=user,
            compliting=True,
            action__in=[
                TalonActions.ASSIGNED,
                TalonActions.STARTED,
            ],
        ).exists()

        if has_active_talon:
            continue

        last_log = (
            user.talon_logs
            .order_by("-created_at")
            .first()
        )

        last_log_at = (
            last_log.created_at
            if last_log is not None
            else None
        )

        settings_updated_at = operator_settings.updated_at

        activity_dates = [
            activity_date
            for activity_date in [
                last_log_at,
                settings_updated_at,
            ]
            if activity_date is not None
        ]

        # Для существующих настроек updated_at всегда заполнен,
        # но оставляем безопасную проверку.
        if activity_dates:
            last_activity_at = max(activity_dates)

            if last_activity_at >= cutoff:
                continue

        with transaction.atomic():
            updated = (
                OperatorSettings.objects
                .filter(
                    pk=operator_settings.pk,
                    location__isnull=False,
                )
                .update(
                    location=None,
                    automatic_assignment=False,
                    updated_at=now,
                )
            )

            if not updated:
                continue

            OperatorQueue.objects.filter(
                user=user
            ).delete()

            released_count += 1

    return released_count
