from django.contrib import admin

from . import models


admin.site.register(models.HelpTheme)


@admin.register(models.Helper)
class HelperAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "sector",
        "is_active",
        "tg_chat_id",
        "max_user_id",
        "max_link_code",
        "updated_at",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "sector",
        "max_user_id",
        "max_link_code",
    )


@admin.register(models.HelpRequest)
class HelpRequestAdmin(admin.ModelAdmin):
    list_display = (
        "helper",
        "theme",
        "priority",
        "completed",
    )