from django.apps import AppConfig


class PeoplequeueConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "peopleQueue"

    def ready(self) -> None:
        from . import signals
        return super().ready()
