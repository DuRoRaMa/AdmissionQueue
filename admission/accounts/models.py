from django.db import transaction
from django.contrib.auth.models import AbstractUser

from peopleQueue.models import OperatorSettings, Talon, TalonLog, TalonActions, TalonPurposes


class CustomUser(AbstractUser):
    @property
    def is_busy(self):
        if self.get_current_operator_talon():
            return True
        return False

    @property
    async def ais_busy(self):
        if await self.aget_current_operator_talon():
            return True
        return False

    def get_started_talons(self):
        return self.talon_logs.filter(action__name="Started").values("talon")

    def get_completed_talons(self):
        return self.talon_logs.filter(action__name="Completed").values("talon")

    def get_current_operator_talon(self) -> Talon | None:
        try:
            res = Talon.objects.filter(
                action__in=[TalonActions.ASSIGNED, TalonActions.STARTED],
                updated_by=self,
                compliting=True
            ).get()
            return res
        except Talon.DoesNotExist:
            return None

    async def aget_current_operator_talon(self) -> Talon | None:
        try:
            res = await TalonLog.objects.exclude(
                action__in=[TalonActions.COMPLETED,
                            TalonActions.CANCELLED]).filter(
                                talon__compliting=True,
                                action=TalonActions.ASSIGNED,
                                created_by=self
            ).select_related('talon').aget()

            return res.talon
        except TalonLog.DoesNotExist:
            return None

    def is_assigned_talon(self):
        if self.get_current_operator_talon():
            return True
        return False

    def assign_talon(self) -> None | Talon:
        try:
            with transaction.atomic():
                talon = Talon.objects.filter(
                    action=TalonActions.CREATED,
                    compliting=False,
                    purpose__in=self.operator_settings.purposes.all()
                ).first()
                if talon is None:
                    return None
                talon.refresh_from_db(fields=['action', 'compliting'])
                if talon.compliting:
                    raise Exception("Talon is already compliting")
                talon.compliting = True
                if talon.action == TalonActions.ASSIGNED:
                    raise Exception("Talon is already assigned")
                talon.action = TalonActions.ASSIGNED
                talon.updated_by = self
                talon.save()
                TalonLog(talon=talon,
                         action=TalonActions.ASSIGNED,
                         created_by=self).save()
        except Exception as e:
            print(e)
            return None
        return talon
