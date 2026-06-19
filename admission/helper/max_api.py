from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from peopleQueue.max_api import IsMaxBotService
from . import models
from . import serializers


MAX_LINK_CODE_TTL_MINUTES = 15


def normalize_code(value: str) -> str:
    return value.strip().upper()


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
    created_by = help_request.created_by

    if created_by is None:
        from_by = "Неизвестный оператор"
    else:
        from_by = created_by.get_full_name() or created_by.get_username()

    return {
        "id": help_request.pk,
        "from": from_by,
        "theme": str(help_request.theme),
        "priority": help_request.get_priority_display(),
        "text": help_request.text,
        "created_at": help_request.created_at.astimezone().strftime(
            "%d.%m.%Y %H:%M"
        ),
    }


def get_helper_by_external_user_id(external_user_id: str):
    return models.Helper.objects.select_related("user").get(
        max_user_id=external_user_id
    )


class MaxHelperLinkAPIView(APIView):
    """
    Привязка MAX-пользователя к Helper по одноразовому коду.
    Вызывается только MAX-ботом.
    """

    authentication_classes = []
    permission_classes = [IsMaxBotService]

    def post(self, request, *args, **kwargs):
        serializer = serializers.MaxHelperLinkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = normalize_code(serializer.validated_data["code"])
        external_user_id = serializer.validated_data["external_user_id"]

        try:
            helper = models.Helper.objects.select_related("user").get(
                max_link_code=code
            )
        except models.Helper.DoesNotExist:
            return Response(
                {"detail": "Код привязки MAX не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if helper.max_link_code_created_at is None:
            return Response(
                {"detail": "Код привязки MAX недействителен."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        expires_at = helper.max_link_code_created_at + timedelta(
            minutes=MAX_LINK_CODE_TTL_MINUTES
        )

        if timezone.now() > expires_at:
            helper.max_link_code = None
            helper.max_link_code_created_at = None
            helper.save(
                update_fields=[
                    "max_link_code",
                    "max_link_code_created_at",
                    "updated_at",
                ]
            )

            return Response(
                {"detail": "Код привязки MAX истек. Сгенерируйте новый код."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        already_linked_helper = (
            models.Helper.objects.filter(max_user_id=external_user_id)
            .exclude(pk=helper.pk)
            .first()
        )

        if already_linked_helper is not None:
            return Response(
                {
                    "detail": (
                        "Этот пользователь MAX уже привязан "
                        "к другому помощнику."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        helper.max_user_id = external_user_id
        helper.max_link_code = None
        helper.max_link_code_created_at = None
        helper.save(
            update_fields=[
                "max_user_id",
                "max_link_code",
                "max_link_code_created_at",
                "updated_at",
            ]
        )

        return Response(
            {
                "detail": "MAX успешно привязан к помощнику.",
                "helper": serialize_helper(helper),
            },
            status=status.HTTP_200_OK,
        )


class MaxHelperProfileAPIView(APIView):
    authentication_classes = []
    permission_classes = [IsMaxBotService]

    def get(self, request, *args, **kwargs):
        external_user_id = request.GET.get("external_user_id", "")

        if not external_user_id:
            return Response(
                {"detail": "Не указан external_user_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            helper = get_helper_by_external_user_id(external_user_id)
        except models.Helper.DoesNotExist:
            return Response(
                {"detail": "MAX-пользователь не привязан к помощнику."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"helper": serialize_helper(helper)})


class MaxHelperToggleActiveAPIView(APIView):
    authentication_classes = []
    permission_classes = [IsMaxBotService]

    def post(self, request, *args, **kwargs):
        serializer = serializers.MaxExternalUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        external_user_id = serializer.validated_data["external_user_id"]

        try:
            helper = get_helper_by_external_user_id(external_user_id)
        except models.Helper.DoesNotExist:
            return Response(
                {"detail": "MAX-пользователь не привязан к помощнику."},
                status=status.HTTP_404_NOT_FOUND,
            )

        helper.is_active = not helper.is_active
        helper.save(update_fields=["is_active", "updated_at"])

        return Response(
            {
                "detail": "Статус помощника обновлен.",
                "helper": serialize_helper(helper),
            },
            status=status.HTTP_200_OK,
        )


class MaxHelperActiveRequestsAPIView(APIView):
    authentication_classes = []
    permission_classes = [IsMaxBotService]

    def get(self, request, *args, **kwargs):
        external_user_id = request.GET.get("external_user_id", "")

        if not external_user_id:
            return Response(
                {"detail": "Не указан external_user_id."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            helper = get_helper_by_external_user_id(external_user_id)
        except models.Helper.DoesNotExist:
            return Response(
                {"detail": "MAX-пользователь не привязан к помощнику."},
                status=status.HTTP_404_NOT_FOUND,
            )

        requests = (
            models.HelpRequest.objects.select_related("created_by", "theme")
            .filter(helper=helper, completed=False)
            .order_by("-created_at")
        )

        return Response(
            {
                "requests": [
                    serialize_help_request(help_request)
                    for help_request in requests
                ]
            },
            status=status.HTTP_200_OK,
        )


class MaxHelperCompleteRequestAPIView(APIView):
    authentication_classes = []
    permission_classes = [IsMaxBotService]

    def post(self, request, request_id: int, *args, **kwargs):
        serializer = serializers.MaxExternalUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        external_user_id = serializer.validated_data["external_user_id"]

        try:
            helper = get_helper_by_external_user_id(external_user_id)
        except models.Helper.DoesNotExist:
            return Response(
                {"detail": "MAX-пользователь не привязан к помощнику."},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            help_request = models.HelpRequest.objects.get(
                pk=request_id,
                helper=helper,
            )
        except models.HelpRequest.DoesNotExist:
            return Response(
                {"detail": "Заявка помощи не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if help_request.completed:
            return Response(
                {"detail": "Заявка уже была выполнена."},
                status=status.HTTP_200_OK,
            )

        help_request.completed = True
        help_request.save(update_fields=["completed", "updated_at"])

        return Response(
            {"detail": "Заявка помощи отмечена как выполненная."},
            status=status.HTTP_200_OK,
        )