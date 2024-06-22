import logging
from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from accounts.authentication import BearerAuthentication

from .serializers import OperatorLocationSerializer, OperatorSettingsSerializer, TalonPurposesSerializer, TalonSerializer, TalonLogSerializer
from .models import OperatorLocation, OperatorSettings, Talon, TalonLog, TalonPurposes

channel_layer = get_channel_layer()


class OperatorTalonActionAPIView(APIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication,
                              BearerAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> JsonResponse | Response:
        action = request.GET.get('action')
        talon = request.user.get_current_operator_talon()
        if action == "next" and talon is None:
            talon = request.user.assign_talon()
            if talon:
                return JsonResponse(data={'id': talon.id}, status=200)
            else:
                return JsonResponse(data={'id': None}, status=200)
        elif action == "current":
            if talon:
                return JsonResponse(data={'id': talon.id}, status=200)
            return JsonResponse(data={'id': None}, status=200)
        else:
            return Response(status=400)

    def post(self, request):
        action = request.GET.get('action')
        logging.info(action)
        settings = OperatorSettings.objects.get(user=request.user)
        talon = request.user.get_current_operator_talon()
        if not talon:
            return Response(status=400)
        if action == 'start':
            TalonLog(
                talon=talon,
                action=TalonLog.Actions.STARTED,
                created_by=request.user
            ).save()
            return Response(status=200)
        elif action == 'cancel':
            talon.compliting = False
            talon.save()
            TalonLog(
                talon=talon,
                action=TalonLog.Actions.CANCELLED,
                created_by=request.user
            ).save()
            if settings.automatic_assignment:
                request.user.assign_talon()
            return Response(status=200)
        elif action == 'complete':
            talon.compliting = False
            talon.save()
            TalonLog(
                talon=talon,
                action=TalonLog.Actions.COMPLETED,
                created_by=request.user
            ).save()
            if settings.automatic_assignment:
                request.user.assign_talon()
            return Response(status=200)
        elif action == 'notify':
            log: TalonLog | None = TalonLog.objects.filter(
                talon=talon,
                action=TalonLog.Actions.ASSIGNED
            ).last()
            if log is None:
                return Response(status=400)
            async_to_sync(channel_layer.group_send)(
                'tablo',
                {
                    "type": 'talonLog.create',
                    'message': log.pk
                }
            )
            return Response(status=200)
        else:
            return Response(status=400)


class TalonListCreateAPIView(generics.ListCreateAPIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = Talon.objects.all()
    serializer_class = TalonSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        log = TalonLogSerializer(
            data={'talon': instance.pk,
                  'action': TalonLog.Actions.CREATED,
                  'comment': request.data.get('comment', ''),
                  'created_by': request.user.pk}
        )
        log.is_valid(raise_exception=True)
        log.save()
        return JsonResponse(data={'id': instance.pk}, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        d = serializer.validated_data
        ordinal = 1
        f = Talon.get_active_queryset().filter(purpose=d.get('purpose')).last()
        if f:
            ordinal += f.ordinal
        code = d.get('purpose').code
        num = "{:2d}".format(ordinal).replace(' ', '0')
        name = f"{code} - {num}"
        return serializer.save(name=name, ordinal=ordinal)


class OperatorInfoListAPIView(generics.views.APIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        purposes = TalonPurposesSerializer(
            TalonPurposes.objects.all(), many=True).data
        locations = OperatorLocationSerializer(
            OperatorLocation.objects.all(), many=True).data
        return JsonResponse({'purposes': purposes, 'locations': locations}, status=200)


class TabloAPIView(generics.GenericAPIView):
    serializer_class = TalonLogSerializer

    def get(self, request):
        q = Talon.get_active_queryset()
        # type: ignore
        return Response(data=TalonLogSerializer(q.logs(), many=True).data, status=200)


class OperatorSettingsAPIView(generics.GenericAPIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = OperatorSettings.objects.all()
    serializer_class = OperatorSettingsSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        query = self.queryset.filter(user=user)
        try:
            instance = query.get()
        except OperatorSettings.DoesNotExist:
            instance = OperatorSettings(user=user)
            instance.save()
        serializer = self.get_serializer(instance)
        return JsonResponse(serializer.data, status=200)

    def patch(self, request, *args, **kwargs):
        user = request.user
        query = self.queryset.filter(user=user)
        try:
            instance = query.get()
        except OperatorSettings.DoesNotExist:
            instance = OperatorSettings(user=user)
            instance.save()
        serializer = self.get_serializer(
            instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)
