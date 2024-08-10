from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(OperatorQueue)


@admin.register(Talon)
class TalonAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'purpose', 'action', 'updated_by', 'compliting',
                    'tg_chat_id', 'updated_at', 'created_at')
    list_filter = ('purpose', 'compliting', 'action')


@admin.register(TalonLog)
class TalonLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'talon', 'action', 'created_by',
                    'created_at')


@admin.register(TalonPurposes)
class TalonPurposesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code', 'updated_at', 'created_at')


@admin.register(OperatorLocation)
class OperatorLocationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'updated_at', 'created_at')


@admin.register(OperatorSettings)
class OperatorSettingsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'location',
                    'automatic_assignment', 'updated_at', 'created_at')
