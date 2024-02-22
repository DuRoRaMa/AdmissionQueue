from django.db import models

# Create your models here.
class Talon(models.Model):
    name = models.CharField(max_length=5)
    createdAt = models.DateTimeField(auto_now_add=True)