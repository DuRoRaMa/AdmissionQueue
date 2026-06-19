import secrets
import string

from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated

from accounts.authentication import BearerAuthentication
from . import models
from . import serializers


MAX_LINK_CODE_LENGTH = 6
MAX_LINK_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def generate_unique_max_link_code() -> str:
    for _ in range(30):
        code = "".join(
            secrets.choice(MAX_LINK_CODE_ALPHABET)
            for _ in range(MAX_LINK_CODE_LENGTH)
        )

        if not models.Helper.objects.filter(max_link_code=code).exists():
            return code

    raise RuntimeError("Не удалось сгенерировать уникальный код привязки MAX")


class HelpInfoListAPIView(generics.views.APIView):
    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
        BearerAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        helpers = serializers.HelperSerializer(
            models.Helper.objects.filter(is_active=True),
            many=True,
        ).data

        themes = serializers.HelpThemeSerializer(
            models.HelpTheme.objects.all(),
            many=True,
        ).data

        return JsonResponse(
            {
                "helpers": helpers,
                "themes": themes,
            },
            status=200,
        )


class HelpRequestCreateAPIView(generics.CreateAPIView):
    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
        BearerAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    queryset = models.HelpRequest.objects.all()
    serializer_class = serializers.HelpRequestSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class HelperMaxLinkCodeAPIView(APIView):
    """
    Генерирует одноразовый код привязки MAX для текущего помощника.

    Пользователь должен быть авторизован в web-системе и иметь запись Helper.
    """

    authentication_classes = [
        SessionAuthentication,
        BasicAuthentication,
        BearerAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            helper = models.Helper.objects.select_related("user").get(
                user=request.user
            )
        except models.Helper.DoesNotExist:
            return Response(
                {
                    "detail": "Для текущего пользователя не найден профиль помощника."
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        code = generate_unique_max_link_code()

        helper.max_link_code = code
        helper.max_link_code_created_at = timezone.now()
        helper.save(
            update_fields=[
                "max_link_code",
                "max_link_code_created_at",
                "updated_at",
            ]
        )

        return Response(
            {
                "code": code,
                "command": f"/link {code}",
                "detail": "Отправьте эту команду MAX-боту электронной очереди.",
            },
            status=status.HTTP_200_OK,
        )