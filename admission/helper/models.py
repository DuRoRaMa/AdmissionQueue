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


class HelpRequest(models.Model):
    PRIORITIES = {
        'Low': "Низкая",
        'Medium': 'Средняя',
        'High': 'Высокая',
    }
    helper = models.ForeignKey(Helper, on_delete=models.CASCADE)
    text = models.TextField()
    priority = models.CharField(max_length=6, choices=PRIORITIES)
    completed = models.BooleanField(default=False)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
