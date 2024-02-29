from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Talon(models.Model):
    name = models.CharField(max_length=5)
    compliting_by = models.OneToOneField(User, related_name="compliting_talon", default=None, on_delete=models.SET_NULL, null=True)
    completed = models.BooleanField(default=False)
    completed_by = models.ForeignKey(User, related_name="completed_talons", default=None, on_delete=models.SET_NULL, null=True)
    completed_at = models.DateTimeField(default=None, null=True)
    updated_by = models.ForeignKey(User, related_name="talons_updated", on_delete=models.SET_NULL, null=True)
    updated_at= models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, related_name="talons_created", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)