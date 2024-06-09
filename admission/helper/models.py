from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.


class Helper(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    sector = models.CharField(max_length=50)
    is_active = models.BooleanField(default=False)
    tg_chat_id = models.IntegerField(default=None, null=True)
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
        'Low': "Низкая",
        'Medium': 'Средняя',
        'High': 'Высокая',
    }
    helper = models.ForeignKey(Helper, on_delete=models.SET_NULL, null=True)
    theme = models.ForeignKey(HelpTheme, on_delete=models.PROTECT)
    text = models.TextField(blank=True)
    priority = models.CharField(max_length=6, choices=PRIORITIES)
    completed = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.helper} - {self.theme} - {self.priority}"
