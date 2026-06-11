from rest_framework.permissions import BasePermission


class IsQueueAdmin(BasePermission):
    """
    Разрешает доступ только пользователям группы Admins.
    """

    message = "Доступ к общей статистике разрешён только администраторам."

    def has_permission(self, request, view) -> bool:
        user = request.user

        return bool(
            user
            and user.is_authenticated
            and user.groups.filter(name="Admins").exists()
        )