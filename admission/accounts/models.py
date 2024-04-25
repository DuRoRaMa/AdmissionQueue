from django.db import models
from django.contrib.auth.models import AbstractUser

from peopleQueue.models import Talon


class CustomUser(AbstractUser):
    def get_started_talons(self):
        return self.talon_logs.filter(action__name="Started").values("talon")

    def get_completed_talons(self):
        return self.talon_logs.filter(action__name="Completed").values("talon")

    def get_current_talon(self) -> Talon | None:
        """Если существует запись в таблице логов о старте талона и не существует о конце, то передается талон, если же запись о конце существует, то возвращается None

        Returns:
            Talon | None
        """
        if self.talon_logs.filter(action__name="Started").exists():
            last_talon = self.talon_logs.filter(
                action__name="Started").last().talon
            if last_talon.is_over():
                return None
            else:
                return last_talon
        else:
            return None
