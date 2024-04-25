from django.db import models
from django.conf import settings


class TalonPurposes(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10)
    description = models.TextField()

    def __str__(self):
        return f"({self.code}) {self.name}"


class TalonAction(models.Model):
    # Created, Started, Completed, Canceled, Redirected
    name = models.CharField(max_length=10)
    description = models.TextField(default="", blank=True)

    def __str__(self):
        return self.name


class Talon(models.Model):
    name = models.CharField(max_length=10)
    purpose = models.ForeignKey(TalonPurposes, on_delete=models.DO_NOTHING)

    def get_last_action(self) -> TalonAction:
        return self.logs.order_by("created_at").last()

    def is_over(self) -> bool:
        return self.is_cancelled() or self.is_completed()

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


class TalonLog(models.Model):
    talon = models.ForeignKey(
        Talon, related_name="logs", on_delete=models.CASCADE)
    action = models.ForeignKey(
        TalonAction, related_name="logs", on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="talon_logs", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class OperatorLocation(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class OperatorSettings(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name="operator_settings", on_delete=models.CASCADE)
    location = models.OneToOneField(
        OperatorLocation, related_name="settings", on_delete=models.SET_NULL, null=True, default=None)
    purposes = models.ManyToManyField(TalonPurposes, blank=True)

    def __str__(self):
        return f"Настройки {self.user.username}"
