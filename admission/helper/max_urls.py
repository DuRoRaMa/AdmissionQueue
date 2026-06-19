from django.urls import path

from .max_api import (
    MaxHelperMeAPIView,
    MaxHelperRequestCompleteAPIView,
    MaxHelperRequestsAPIView,
    MaxHelperToggleActiveAPIView,
)

urlpatterns = [
    path("me/", MaxHelperMeAPIView.as_view(), name="max-helper-me"),
    path(
        "toggle-active/",
        MaxHelperToggleActiveAPIView.as_view(),
        name="max-helper-toggle-active",
    ),
    path(
        "requests/",
        MaxHelperRequestsAPIView.as_view(),
        name="max-helper-requests",
    ),
    path(
        "requests/<int:request_id>/complete/",
        MaxHelperRequestCompleteAPIView.as_view(),
        name="max-helper-request-complete",
    ),
]