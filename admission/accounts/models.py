from django.db import models
from django.contrib.auth.models import AbstractUser

from peopleQueue.models import Talon, TalonLog


class CustomUser(AbstractUser):
    def get_started_talons(self):
        return self.talon_logs.filter(action__name="Started").values("talon")

    def get_completed_talons(self):
        return self.talon_logs.filter(action__name="Completed").values("talon")

    def get_current_operator_talon(self) -> Talon | None:
        # return Talon.objects.exclude(
        #     logs__action__in=[TalonLog.Actions.COMPLETED,
        #                       TalonLog.Actions.CANCELLED],
        #     compliting=True).filter(
        #     logs__action=TalonLog.Actions.ASSIGNED, logs__created_by=self
        # ).last()
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
