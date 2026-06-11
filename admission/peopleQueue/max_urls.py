from django.urls import path

from .max_api import (
    MaxTalonCommentAPIView,
    MaxTalonDetailAPIView,
    MaxTalonListAPIView,
    MaxTalonSubscribeAPIView,
)

urlpatterns = [
    path(
        "talons/subscribe/",
        MaxTalonSubscribeAPIView.as_view(),
        name="max-talon-subscribe",
    ),
    path(
        "talons/",
        MaxTalonListAPIView.as_view(),
        name="max-talon-list",
    ),
    path(
        "talons/<int:talon_id>/",
        MaxTalonDetailAPIView.as_view(),
        name="max-talon-detail",
    ),
    path(
        "talons/<int:talon_id>/comment/",
        MaxTalonCommentAPIView.as_view(),
        name="max-talon-comment",
    ),
]
