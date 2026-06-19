import secrets

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from peopleQueue.models import OperatorSettings
from . import models


class IsMaxBotService(BasePermission):
    message = "Недействительный внутренний токен."

    def has_permission(self, request, view) -> bool:
        supplied = request.headers.get("X-Internal-Token", "")
        expected = getattr(settings, "MAX_BOT_INTERNAL_TOKEN", "")
        return bool(expected and secrets.compare_digest(supplied, expected))


class MaxBotInternalAPIView(APIView):
    authentication_classes = []
    permission_classes = [IsMaxBotService]


class MaxExternalUserSerializer(serializers.Serializer):
    external_user_id = serializers.CharField(max_length=128)


class MaxHelperRequestCompleteSerializer(serializers.Serializer):
    external_user_id = serializers.CharField(max_length=128)


def get_helper_or_404(external_user_id: str) -> models.Helper:
    return get_object_or_404(
        models.Helper.objects.select_related("user"),
        max_user_id=external_user_id,
    )


def get_operator_title(user) -> str:
    if user is None:
        return "Неизвестно"

    name = user.get_full_name() or user.get_username() or str(user)
    operator_settings = (
        OperatorSettings.objects
        .select_related("location")
        .filter(user=user)
        .first()
    )

    if operator_settings and operator_settings.location:
        return f"{name} (Стол {operator_settings.location.name})"

    return name


def serialize_helper(helper: models.Helper) -> dict:
    return {
        "id": helper.pk,
        "username": helper.user.get_username(),
        "full_name": helper.user.get_full_name(),
        "sector": helper.sector,
        "is_active": helper.is_active,
        "active_requests_count": models.HelpRequest.objects.filter(
            helper=helper,
            completed=False,
        ).count(),
    }


def serialize_help_request(help_request: models.HelpRequest) -> dict:
    return {
        "id": help_request.pk,
        "from": get_operator_title(help_request.created_by),
        "theme": str(help_request.theme),
        "priority": help_request.get_priority_display(),
        "text": help_request.text or "",
        "created_at": help_request.created_at.astimezone().strftime(
            "%d.%m.%Y %H:%M"
        ),
    }


class MaxHelperMeAPIView(MaxBotInternalAPIView):
    def get(self, request: Request) -> Response:
        serializer = MaxExternalUserSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        helper = get_helper_or_404(
            serializer.validated_data["external_user_id"]
        )
        return Response(serialize_helper(helper), status=status.HTTP_200_OK)


class MaxHelperToggleActiveAPIView(MaxBotInternalAPIView):
    def post(self, request: Request) -> Response:
        serializer = MaxExternalUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        helper = get_helper_or_404(
            serializer.validated_data["external_user_id"]
        )
        helper.is_active = not helper.is_active
        helper.save(update_fields=["is_active", "updated_at"])

        return Response(serialize_helper(helper), status=status.HTTP_200_OK)


class MaxHelperRequestsAPIView(MaxBotInternalAPIView):
    def get(self, request: Request) -> Response:
        serializer = MaxExternalUserSerializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        helper = get_helper_or_404(
            serializer.validated_data["external_user_id"]
        )
        requests = (
            models.HelpRequest.objects
            .select_related("created_by", "theme")
            .filter(helper=helper, completed=False)
            .order_by("-created_at")
        )

        return Response(
            {"requests": [serialize_help_request(item) for item in requests]},
            status=status.HTTP_200_OK,
        )


class MaxHelperRequestCompleteAPIView(MaxBotInternalAPIView):
    def post(self, request: Request, request_id: int) -> Response:
        serializer = MaxHelperRequestCompleteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        helper = get_helper_or_404(
            serializer.validated_data["external_user_id"]
        )
        help_request = get_object_or_404(
            models.HelpRequest.objects.select_related("helper", "theme", "created_by"),
            pk=request_id,
            helper=helper,
        )

        if not help_request.completed:
            help_request.completed = True
            help_request.save(update_fields=["completed", "updated_at"])

        return Response(
            {
                "id": help_request.pk,
                "completed": help_request.completed,
                "detail": "Заявка помощи выполнена.",
            },
            status=status.HTTP_200_OK,
        )