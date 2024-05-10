import datetime
from django.contrib.auth.mixins import LoginRequiredMixin
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from accounts.authentication import BearerAuthentication

from .serializers import OperatorLocationSerializer, OperatorSettingsSerializer, TalonPurposesSerializer, TalonSerializer, TalonLogSerializer
from .models import OperatorLocation, OperatorSettings, Talon, TalonLog, TalonPurposes

channel_layer = get_channel_layer()


class OperatorAPIView(APIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = TalonSerializer

    def get(self, request):
        talon = Talon.objects.filter(
            completed=False, compliting_by__isnull=True).order_by("created_at")[0]
        talon.compliting_by = self.request.user
        talon.save()
        serializer = TalonSerializer(talon)
        async_to_sync(channel_layer.group_send)(
            "tablo", {
                "type": "talon_update",
                "message": serializer.data
            }
        )
        return Response(serializer.data, status=200)

    def post(self, request):
        talon = self.request.user.compliting_talon
        if talon is None:
            return Response(data={"errors": ['You do not do talon right now']}, status=400)
        talon.completed = True
        talon.completed_at = datetime.datetime.now()
        talon.completed_by = self.request.user
        talon.compliting_by = None
        talon.save()
        async_to_sync(channel_layer.group_send)(
            "tablo", {
                "type": "talon_remove",
                "message": TalonSerializer(talon).data
            }
        )
        return Response(status=200)


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
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        d = serializer.validated_data
        ordinal = 1
        f = Talon.objects.filter(purpose=d.get('purpose')).exclude(logs__action__in=[
            TalonLog.Actions.COMPLETED, TalonLog.Actions.CANCELLED]).last()
        if f:
            ordinal += f.ordinal
        name = f"{d.get('purpose').code}{
            ordinal}"
        return serializer.save(name=name, ordinal=ordinal)


class OperatorLocationListAPIView(generics.ListAPIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = OperatorLocation.objects.all()
    serializer_class = OperatorLocationSerializer


class TalonPurposesListAPIView(generics.ListAPIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = TalonPurposes.objects.all()
    serializer_class = TalonPurposesSerializer


class TabloAPIView(generics.GenericAPIView):
    serializer_class = TalonLogSerializer

    def get(self, request):
        q = Talon.objects.exclude(logs__action__name__in=[
                                  "Completed", "Cancelled"])
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
        return Response(serializer.data)

    def patch(self, request, *args, **kwargs):
        user = request.user
        query = self.queryset.filter(user=user)
        try:
            instance = query.get()
            serializer = self.get_serializer(
                instance, data=request.data, partial=True)
        except OperatorSettings.DoesNotExist:
            serializer = self.get_serializer(user=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)
