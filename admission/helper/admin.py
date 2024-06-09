from django.contrib import admin

from . import models

# Register your models here.
admin.site.register(models.HelpTheme)


@admin.register(models.Helper)
class HelperAdmin(admin.ModelAdmin):
    list_display = ('user', 'sector', 'is_active',
                    'tg_chat_id', 'updated_at', 'created_at')


@admin.register(models.HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = ('helper', 'theme', 'priority', 'completed')
