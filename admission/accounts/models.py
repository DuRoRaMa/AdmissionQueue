from django.db import models
from django.contrib.auth.models import AbstractUser

from peopleQueue.models import Talon, TalonLog


class CustomUser(AbstractUser):
    def get_started_talons(self):
        return self.talon_logs.filter(action__name="Started").values("talon")

    def get_completed_talons(self):
        return self.talon_logs.filter(action__name="Completed").values("talon")

    def get_current_operator_talon(self) -> Talon | None:
        try:
            res = TalonLog.objects.exclude(
                action__in=[TalonLog.Actions.COMPLETED,
                            TalonLog.Actions.CANCELLED]).filter(
                                talon__compliting=True,
                                action=TalonLog.Actions.ASSIGNED,
                                created_by=self
            ).select_related('talon').get()

            return res.talon
        except TalonLog.DoesNotExist:
            return None

    async def aget_current_operator_talon(self) -> Talon | None:
        try:
            res = await TalonLog.objects.exclude(
                action__in=[TalonLog.Actions.COMPLETED,
                            TalonLog.Actions.CANCELLED]).filter(
                                talon__compliting=True,
                                action=TalonLog.Actions.ASSIGNED,
                                created_by=self
            ).select_related('talon').aget()

            return res.talon
        except TalonLog.DoesNotExist:
            return None

    def is_assigned_talon(self):
        if self.get_current_operator_talon():
            return True
        return False

    def assign_talon(self):
        talon = Talon.get_active_queryset().filter(
            compliting=False,
            purpose__in=self.operator_settings.purposes.all()
        ).first()
        if talon is None:
            return None
        talon.compliting = True
        talon.save()
        TalonLog(talon=talon,
                 action=TalonLog.Actions.ASSIGNED,
                 created_by=self).save()
        return talon

    async def aassign_talon(self):
        talon = await Talon.get_active_queryset().filter(
            compliting=False,
            purpose__in=self.operator_settings.purposes.all()
        ).afirst()
        if talon is None:
            return None
        talon.compliting = True
        await talon.asave()
        await TalonLog(talon=talon,
                       action=TalonLog.Actions.ASSIGNED,
                       created_by=self).asave()
        return talon
