from django.urls import re_path

from .consumers.operator_notifications import OperatorNotificationsConsumer


websocket_urlpatterns = [
    re_path(
        r"ws/operator/notifications/$",
        OperatorNotificationsConsumer.as_asgi(),
    ),
]