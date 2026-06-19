from django.db import models
from django.contrib.auth import get_user_model


class Helper(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    sector = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)

    tg_chat_id = models.IntegerField(default=None, null=True)

    max_user_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        verbose_name="MAX ID помощника",
    )

    max_link_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        verbose_name="Код привязки MAX",
    )

    max_link_code_created_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name="Дата создания кода привязки MAX",
    )

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}"


class HelpTheme(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(null=True)

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class HelpRequest(models.Model):
    PRIORITIES = {
        "Low": "Низкая",
        "Medium": "Средняя",
        "High": "Высокая",
    }

    helper = models.ForeignKey(Helper, on_delete=models.SET_NULL, null=True)
    theme = models.ForeignKey(HelpTheme, on_delete=models.PROTECT)
    text = models.TextField(blank=True)
    priority = models.CharField(max_length=6, choices=PRIORITIES)
    completed = models.BooleanField(default=False)

    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
    )

    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.helper} - {self.theme} - {self.priority}"