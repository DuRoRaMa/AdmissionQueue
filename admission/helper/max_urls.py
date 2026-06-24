from django.urls import path

from . import max_api


urlpatterns = [
    path(
        "link-code/",
        max_api.MaxHelperLinkAPIView.as_view(),
        name="max-helper-link-code",
    ),
    path(
        "me/",
        max_api.MaxHelperProfileAPIView.as_view(),
        name="max-helper-profile",
    ),
    path(
        "toggle-active/",
        max_api.MaxHelperToggleActiveAPIView.as_view(),
        name="max-helper-toggle-active",
    ),
    path(
        "requests/",
        max_api.MaxHelperActiveRequestsAPIView.as_view(),
        name="max-helper-active-requests",
    ),
    path(
        "requests/<int:request_id>/complete/",
        max_api.MaxHelperCompleteRequestAPIView.as_view(),
        name="max-helper-complete-request",
    ),
]