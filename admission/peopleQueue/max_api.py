import secrets

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import serializers, status
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Talon,
    TalonActions,
    TalonMessengerSubscription,
)


STATUS_LABELS = {
    TalonActions.CREATED: "В ожидании",
    TalonActions.ASSIGNED: "Оператор ожидает вас",
    TalonActions.STARTED: "В процессе",
    TalonActions.COMPLETED: "Завершён",
    TalonActions.CANCELLED: "Отменён",
    TalonActions.REDIRECTED: "В ожидании",
}


class IsMaxBotService(BasePermission):
    message = "Недействительный внутренний токен."

    def has_permission(self, request, view) -> bool:
        supplied = request.headers.get(
            "X-Internal-Token",
            "",
        )
        expected = getattr(
            settings,
            "MAX_BOT_INTERNAL_TOKEN",
            "",
        )

        return bool(
            expected
            and secrets.compare_digest(
                supplied,
                expected,
            )
        )

class MaxBotInternalAPIView(APIView):
    authentication_classes = []
    permission_classes = [IsMaxBotService]

class MaxSubscribeSerializer(serializers.Serializer):
    external_user_id = serializers.CharField(
        max_length=128
    )
    talon_id = serializers.IntegerField(
        min_value=1
    )


class MaxCommentSerializer(serializers.Serializer):
    external_user_id = serializers.CharField(
        max_length=128
    )
    comment = serializers.CharField(
        max_length=5000,
        allow_blank=False,
        trim_whitespace=True,
    )


def serialize_talon(talon: Talon) -> dict:
    return {
        "id": talon.pk,
        "name": talon.name,
        "status": talon.action,
        "status_label": STATUS_LABELS.get(
            talon.action,
            talon.action,
        ),
        "created_at": (
            talon.created_at
            .astimezone()
            .strftime("%d.%m.%Y %H:%M")
        ),
        "comment": talon.comment,
        "purpose": {
            "id": talon.purpose_id,
            "name": talon.purpose.name,
        },
    }


def get_owned_talon(
    *,
    external_user_id: str,
    talon_id: int,
) -> Talon:
    return get_object_or_404(
        Talon.objects.select_related(
            "purpose"
        ),
        pk=talon_id,
        messenger_subscriptions__provider="max",
        messenger_subscriptions__external_user_id=(
            external_user_id
        ),
    )


class MaxTalonSubscribeAPIView(MaxBotInternalAPIView):
    permission_classes = [IsMaxBotService]

    def post(self, request: Request) -> Response:
        serializer = MaxSubscribeSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        external_user_id = serializer.validated_data[
            "external_user_id"
        ]
        talon_id = serializer.validated_data[
            "talon_id"
        ]

        talon = get_object_or_404(
            Talon.objects.select_related("purpose"),
            pk=talon_id,
        )

        existing = (
            TalonMessengerSubscription.objects
            .filter(
                talon=talon,
                provider="max",
            )
            .first()
        )

        if (
            existing is not None
            and existing.external_user_id
            != external_user_id
        ):
            return Response(
                {
                    "detail": (
                        "Данный талон уже подключён "
                        "к другому пользователю MAX."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        TalonMessengerSubscription.objects.update_or_create(
            talon=talon,
            provider="max",
            defaults={
                "external_user_id": (
                    external_user_id
                )
            },
        )

        return Response(
            {
                "id": talon.pk,
                "name": talon.name,
                "detail": "Подписка оформлена.",
            },
            status=status.HTTP_200_OK,
        )


class MaxTalonListAPIView(MaxBotInternalAPIView):
    permission_classes = [IsMaxBotService]

    def get(self, request: Request) -> Response:
        external_user_id = request.GET.get(
            "external_user_id",
            "",
        )

        if not external_user_id:
            return Response(
                {
                    "detail": (
                        "Не указан external_user_id."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        talons = (
            Talon.objects
            .filter(
                messenger_subscriptions__provider="max",
                messenger_subscriptions__external_user_id=(
                    external_user_id
                ),
            )
            .select_related("purpose")
            .order_by("-created_at")
        )

        return Response(
            {
                "talons": [
                    serialize_talon(talon)
                    for talon in talons
                ]
            }
        )


class MaxTalonDetailAPIView(MaxBotInternalAPIView):
    permission_classes = [IsMaxBotService]

    def get(
        self,
        request: Request,
        talon_id: int,
    ) -> Response:
        external_user_id = request.GET.get(
            "external_user_id",
            "",
        )

        talon = get_owned_talon(
            external_user_id=external_user_id,
            talon_id=talon_id,
        )

        return Response(serialize_talon(talon))


class MaxTalonCommentAPIView(MaxBotInternalAPIView):
    permission_classes = [IsMaxBotService]

    def post(
        self,
        request: Request,
        talon_id: int,
    ) -> Response:
        serializer = MaxCommentSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        external_user_id = serializer.validated_data[
            "external_user_id"
        ]
        comment = serializer.validated_data[
            "comment"
        ]

        talon = get_owned_talon(
            external_user_id=external_user_id,
            talon_id=talon_id,
        )

        if talon.comment:
            return Response(
                {
                    "detail": (
                        "Отзыв для этого талона "
                        "уже оставлен."
                    )
                },
                status=status.HTTP_409_CONFLICT,
            )

        talon.comment = comment
        talon.save(
            update_fields=[
                "comment",
                "updated_at",
            ]
        )

        return Response(serialize_talon(talon))
