from datetime import timedelta

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
    Освобождает стол оператора, если:
    1. у оператора выбран стол;
    2. у оператора нет активного талона;
    3. последний лог оператора старше 60 минут или логов вообще нет.

    Дополнительно отключает automatic_assignment, чтобы оператор без стола
    не продолжал автоматически получать талоны.
    """
    now = timezone.now()
    cutoff = now - timedelta(minutes=OPERATOR_IDLE_TIMEOUT_MINUTES)

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

        if last_log is not None and last_log.created_at >= cutoff:
            continue

        operator_settings.location = None
        operator_settings.automatic_assignment = False
        operator_settings.save(
            update_fields=[
                "location",
                "automatic_assignment",
                "updated_at",
            ]
        )

        OperatorQueue.objects.filter(user=user).delete()

        released_count += 1

    return released_count
