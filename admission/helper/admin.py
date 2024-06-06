from django.contrib import admin

from . import models

# Register your models here.
admin.site.register(models.Helper)
admin.site.register(models.HelpRequest)
