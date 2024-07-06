from django.db import models
from django.conf import settings


class TalonPurposes(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10)
    description = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"id({self.pk}) ({self.code}) {self.name}"


class Talon(models.Model):
    name = models.CharField(max_length=10)
    ordinal = models.IntegerField()
    purpose = models.ForeignKey(TalonPurposes, on_delete=models.DO_NOTHING)
    compliting = models.BooleanField(default=False)
    tg_chat_id = models.BigIntegerField(default=None, null=True)
    comment = models.TextField(null=True, default=None)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def completed_by(self):
        try:
            log = self.logs.filter(action=TalonLog.Actions.COMPLETED).get()
        except TalonLog.DoesNotExist:
            return None
        except TalonLog.MultipleObjectsReturned:
            return None
        user = log.created_by
        return user

    @classmethod
    def get_active_queryset(cls):
        return cls.objects.exclude(
            logs__action__in=[TalonLog.Actions.COMPLETED,
                              TalonLog.Actions.CANCELLED]
        ).order_by('-created_at')

    def get_last_log(self):
        return self.logs.last()

    async def aget_last_log(self):
        return (await self.logs.alast())

    def get_last_action(self):
        return self.logs.last().action

    async def aget_last_action(self):
        return (await self.logs.alast()).action

    def is_over(self) -> bool:
        if self.logs.filter(
                action__in=[
                    TalonLog.Actions.COMPLETED,
                    TalonLog.Actions.CANCELLED
                ]).exists():
            return True
        else:
            return False

    async def ais_over(self) -> bool:
        if await self.logs.filter(
                action__in=[
                    TalonLog.Actions.COMPLETED,
                    TalonLog.Actions.CANCELLED
                ]).aexists():
            return True
        else:
            return False

    def is_cancelled(self) -> bool:
        if self.logs.filter(action__name="Cancelled").exists():
            return True
        else:
            return False

    def is_completed(self) -> bool:
        if self.logs.filter(action__name="Completed").exists():
            return True
        else:
            return False

    def __str__(self):
        return f"Talon(id({self.pk}) {self.name} ({self.purpose.name}))"


class TalonLog(models.Model):
    class Actions(models.TextChoices):
        CREATED = "Created", "Создан"
        ASSIGNED = "Assigned", "Назначен"
        STARTED = "Started", "Запущен"
        COMPLETED = "Completed", "Завершен"
        CANCELLED = "Cancelled", "Отменен"
        REDIRECTED = "Redirected", "Перенаправлен"
    talon = models.ForeignKey(
        Talon, related_name="logs", on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=Actions.choices)
    comment = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="talon_logs", on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"id({self.pk})  {self.talon} - {self.action} {self.created_at} by {self.created_by}"


class OperatorLocation(models.Model):
    name = models.CharField(max_length=30)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'id({self.pk})-{self.name}'


class OperatorSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name="operator_settings", on_delete=models.CASCADE)
    location = models.OneToOneField(
        OperatorLocation, related_name="settings", on_delete=models.SET_NULL, null=True, default=None)
    purposes = models.ManyToManyField(
        TalonPurposes, related_name='operator_settings', blank=True)
    automatic_assignment = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"id({self.pk}) Настройки {self.user.username}"


class OperatorQueue(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="operator_queue", on_delete=models.CASCADE)
    purpose = models.ForeignKey(TalonPurposes, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
