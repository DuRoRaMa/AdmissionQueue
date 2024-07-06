from django.contrib.auth.models import AbstractUser

from peopleQueue.models import OperatorSettings, Talon, TalonLog, TalonPurposes


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
        talon = Talon.objects.exclude(
            logs__action__in=[TalonLog.Actions.COMPLETED,
                              TalonLog.Actions.CANCELLED]).filter(
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
        settings = await OperatorSettings.objects.aget(user=self)
        purposes = [purpose.pk async for purpose in TalonPurposes.objects.filter(operator_settings=settings)]
        # purposes = (await OperatorSettings.objects.prefetch_related('purposes').aget(user=self)).purposes.values_list('pk', flat=True)
        talon = await Talon.objects.exclude(
            action__in=[TalonLog.Actions.COMPLETED,
                        TalonLog.Actions.CANCELLED]).filter(
            compliting=False,
            purpose__in=purposes
        ).afirst()
        if talon is None:
            return None
        talon.compliting = True
        await talon.asave()
        await TalonLog(talon=talon,
                       action=TalonLog.Actions.ASSIGNED,
                       created_by=self).asave()
        return talon
