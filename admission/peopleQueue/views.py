import datetime
import logging
import pytz
from django.http import JsonResponse
from django.db import transaction
from django.conf import settings
from django.db.models import Min, Max, Count, F, Q, FilteredRelation
from django.contrib.auth.models import Group
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .services.operator_activity_service import release_inactive_operator_locations
from accounts.authentication import BearerAuthentication
from accounts.models import CustomUser
from .services.stats_service import (
    get_operator_detailed_statistics,
    get_queue_statistics,
    get_queue_statistics_filters,
)
from .serializers import OperatorLocationSerializer, OperatorSettingsSerializer, TalonPurposesSerializer, TalonSerializer, TalonLogSerializer
from .models import OperatorLocation, OperatorSettings, Talon, TalonLog, TalonPurposes, TalonActions

channel_layer = get_channel_layer()


class OperatorStatsAPIView(APIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication,
                              BearerAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> JsonResponse | Response:
        user = request.user
        current_year = datetime.datetime.now().year
        query = TalonLog.objects.aggregate(
            mi=Min('created_at'),
            ma=Max('created_at')
        )
        min_date: datetime.datetime = query['mi']
        max_date: datetime.datetime = query['ma']
        days = (max_date - min_date).days + 2
        ps = list(map(lambda x: (x['pk'], x['name']),
                  TalonPurposes.objects.values('pk', 'name')))
        obj = Talon.objects.filter(
            logs__action__in=["Completed"],
            logs__created_by=user,
            created_at__year=current_year
        )
        ans = [
            {
                'name': name,
                'data': [
                    [
                        (min_date + datetime.timedelta(days=j)).strftime("%Y-%m-%d"),
                        obj.filter(
                            purpose=i,
                            created_at__day=(
                                min_date + datetime.timedelta(days=j)).day,
                            created_at__month=(
                                min_date + datetime.timedelta(days=j)).month
                        ).count()
                    ] for j in range(days)
                ]
            } for i, name in ps
        ]
        summa = {
            'name': 'Сумма',
            'data': [
                [(min_date + datetime.timedelta(days=j)).strftime("%Y-%m-%d"), sum([d['data'][j][1] for d in ans])] for j in range(days)
            ]
        }
        ans.append(summa)
        return JsonResponse(data=ans, status=200, safe=False)


class OperatorTalonActionAPIView(APIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication,
                              BearerAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> JsonResponse | Response:
        release_inactive_operator_locations()
        action = request.GET.get('action')
        user: CustomUser = request.user
        talon = user.get_current_operator_talon()
        if action == "next" and talon is None:
            talon = user.assign_talon()
            if talon:
                return JsonResponse(data={'id': talon.pk}, status=200)
            else:
                return JsonResponse(data={'id': None}, status=200)
        elif action == "current":
            if talon:
                return JsonResponse(data={'id': talon.pk}, status=200)
            return JsonResponse(data={'id': None}, status=200)
        else:
            return Response(status=400)

    def post(self, request):
        release_inactive_operator_locations()
        user = request.user
        action = request.GET.get('action')
        logging.info(action)
        settings = OperatorSettings.objects.get(user=user)
        talon: Talon | None = request.user.get_current_operator_talon()
        if action == 'new':
            if talon:
                return Response(
                    data={"detail": "У вас уже есть талон в работе"},
                    status=400,
                )

            purpose_id = request.data.get("purpose")
            comment = request.data.get("comment", "")

            if not purpose_id:
                return Response(
                    data={"detail": "Не выбрано направление талона"},
                    status=400,
                )

            with transaction.atomic():
                purpose = TalonPurposes.objects.get(pk=int(purpose_id))

                name, ordinal = Talon.get_name_and_ordinal_new_Talon_by_purpose(
                    purpose
                )

                talon = Talon.objects.create(
                    purpose=purpose,
                    name=name,
                    ordinal=ordinal,
                    action=TalonActions.STARTED,
                    updated_by=user,
                    compliting=True,
                    comment=comment or None,
                )

                TalonLog.objects.create(
                    talon=talon,
                    action=TalonActions.CREATED,
                    comment=comment,
                    created_by=user,
                )

                TalonLog.objects.create(
                    talon=talon,
                    action=TalonActions.ASSIGNED,
                    created_by=user,
                )

                TalonLog.objects.create(
                    talon=talon,
                    action=TalonActions.STARTED,
                    created_by=user,
                )

            return JsonResponse(data={'id': talon.pk}, status=200)

        if not talon:
            return Response(status=400)
        elif action == 'start':
            talon.start_by(user)
            return Response(status=200)
        elif action == 'cancel':
            talon.cancel_by(user)
            return Response(status=200)
        elif action == 'complete':
            talon.complete_by(user)
            return Response(status=200)
        elif action == 'notify':
            log: TalonLog | None = TalonLog.objects.filter(
                talon=talon,
                action=TalonActions.ASSIGNED
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
        elif action == 'redirect':
            if not talon:
                return Response(
                    data={'detail': 'У оператора нет активного талона'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if talon.action not in [TalonActions.ASSIGNED, TalonActions.STARTED]:
                return Response(
                    data={'detail': 'Переадресовать можно только назначенный или начатый талон'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            redirect_mode = request.data.get('mode', 'queue')
            comment = request.data.get('comment', '')

            if redirect_mode not in ['queue', 'operator']:
                return Response(
                    data={'detail': 'Некорректный тип переадресации'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                old_name = talon.name
                old_purpose = talon.purpose

                if redirect_mode == 'queue':
                    purpose_id = request.data.get('purpose')

                    if purpose_id:
                        try:
                            new_purpose = TalonPurposes.objects.get(pk=int(purpose_id))
                        except (TalonPurposes.DoesNotExist, ValueError, TypeError):
                            return Response(
                                data={'detail': 'Новое направление не найдено'},
                                status=status.HTTP_404_NOT_FOUND,
                            )
                    else:
                        new_purpose = old_purpose

                    if new_purpose.pk != old_purpose.pk:
                        new_name, new_ordinal = Talon.get_name_and_ordinal_new_Talon_by_purpose(
                            new_purpose
                        )
                    else:
                        new_name = old_name
                        new_ordinal = talon.ordinal

                    talon.purpose = new_purpose
                    talon.name = new_name
                    talon.ordinal = new_ordinal
                    talon.action = TalonActions.CREATED
                    talon.compliting = False
                    talon.updated_by = user
                    talon.save(
                        update_fields=[
                            'purpose',
                            'name',
                            'ordinal',
                            'action',
                            'compliting',
                            'updated_by',
                            'updated_at',
                        ]
                    )

                    TalonLog.objects.create(
                        talon=talon,
                        action=TalonActions.REDIRECTED,
                        comment=(
                            comment
                            or f'Возвращён в очередь: {old_name} ({old_purpose.name}) → '
                            f'{new_name} ({new_purpose.name})'
                        ),
                        created_by=user,
                    )
                    channel_layer = get_channel_layer()

                    if channel_layer is not None:
                        async_to_sync(channel_layer.group_send)(
                            f"operator_notifications_{target_operator.pk}",
                            {
                                "type": "operator.notification",
                                "data": {
                                    "event": "talon_redirected",
                                    "talon": {
                                        "id": talon.pk,
                                        "name": talon.name,
                                        "purpose": talon.purpose.name,
                                        "action": talon.action,
                                    },
                                    "comment": redirect_comment,
                                    "from_operator": {
                                        "id": user.pk,
                                        "name": user.get_full_name() or user.username,
                                    },
                                },
                            },
                        )
                    return Response(
                        data={
                            'detail': f'Талон возвращён в очередь: {old_name} → {new_name}',
                            'id': talon.pk,
                            'name': talon.name,
                            'mode': 'queue',
                        },
                        status=status.HTTP_200_OK,
                    )

                target_operator_settings_id = request.data.get('operator_settings')

                if not target_operator_settings_id:
                    return Response(
                        data={'detail': 'Не выбран оператор'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                try:
                    target_settings = (
                        OperatorSettings.objects
                        .select_related("user", "location")
                        .get(pk=int(target_operator_settings_id))
                    )
                except (OperatorSettings.DoesNotExist, ValueError, TypeError):
                    return Response(
                        data={'detail': 'Настройки выбранного оператора не найдены'},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                if target_settings.user_id == user.pk:
                    return Response(
                        data={'detail': 'Нельзя переадресовать талон самому себе'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if target_settings.location_id is None:
                    return Response(
                        data={'detail': 'У выбранного оператора не назначено рабочее место'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                target_operator = target_settings.user

                target_has_active_talon = Talon.objects.filter(
                    action__in=[
                        TalonActions.ASSIGNED,
                        TalonActions.STARTED,
                    ],
                    compliting=True,
                    updated_by=target_operator,
                ).exists()

                if target_has_active_talon:
                    return Response(
                        data={'detail': 'Выбранный оператор уже занят'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                talon.action = TalonActions.ASSIGNED
                talon.compliting = True
                talon.updated_by = target_operator
                talon.save(
                    update_fields=[
                        'action',
                        'compliting',
                        'updated_by',
                        'updated_at',
                    ]
                )

                redirect_comment = comment or (
                    f'Переадресован оператору '
                    f'{target_operator.get_full_name() or target_operator.username}'
                )

                TalonLog.objects.create(
                    talon=talon,
                    action=TalonActions.REDIRECTED,
                    comment=redirect_comment,
                    created_by=user,
                )

                TalonLog.objects.create(
                    talon=talon,
                    action=TalonActions.ASSIGNED,
                    comment=(
                        f'Назначен после переадресации от '
                        f'{user.get_full_name() or user.username}. '
                        f'Комментарий: {redirect_comment}'
                    ),
                    created_by=target_operator,
                )

                return Response(
                    data={
                        'detail': (
                            f'Талон {talon.name} передан оператору '
                            f'{target_operator.get_full_name() or target_operator.username}'
                        ),
                        'id': talon.pk,
                        'name': talon.name,
                        'mode': 'operator',
                        'operator': target_operator.pk,
                        'operator_settings': target_settings.pk,
                        'location': target_settings.location.name,
                        'comment': redirect_comment,
                    },
                    status=status.HTTP_200_OK,
                )
        else:
            return Response(status=400)


class RegistratorTalonActionAPIView(APIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication,
                              BearerAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request: Request) -> Response:
        user: CustomUser = request.user
        pk = request.GET.get('id')
        if not user.groups.contains(Group.objects.get(name="Registrators")):
            return Response(status=403, data={'detail': 'Недостаточно прав'})
        with transaction.atomic():
            try:
                talon = Talon.objects.get(pk=pk)
            except Talon.DoesNotExist:
                return Response(status=404, data={'detail': 'Талон не найден'})
            if talon.compliting:
                return Response(status=400, data={'detail': 'Талон в обработке'})
            if talon.action == TalonActions.CANCELLED:
                return Response(status=400, data={'detail': 'Талон уже отменен'})
            talon.cancel_by(user)
        return Response(status=200, data={'detail': f'Талон {talon.name} отменен'})


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
                  'action': TalonActions.CREATED,
                  'comment': request.data.get('comment', ''),
                  'created_by': request.user.pk}
        )
        log.is_valid(raise_exception=True)
        log.save()
        return JsonResponse(data={'id': instance.pk}, status=status.HTTP_201_CREATED, headers=headers)

    def perform_create(self, serializer):
        d = serializer.validated_data
        name, ordinal = Talon.get_name_and_ordinal_new_Talon_by_purpose(
            d.get('purpose'))
        return serializer.save(name=name, ordinal=ordinal, updated_by=self.request.user)


class OperatorInfoListAPIView(generics.views.APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        purposes = TalonPurposesSerializer(
            TalonPurposes.objects.all(),
            many=True,
        ).data

        locations = OperatorLocationSerializer(
            OperatorLocation.objects.all(),
            many=True,
        ).data

        busy_operator_ids = Talon.objects.filter(
            action__in=[
                TalonActions.ASSIGNED,
                TalonActions.STARTED,
            ],
            compliting=True,
            updated_by__isnull=False,
        ).values_list("updated_by_id", flat=True)

        free_operator_settings = (
            OperatorSettings.objects
            .select_related("user", "location")
            .prefetch_related("purposes")
            .filter(location__isnull=False)
            .exclude(user=request.user)
            .exclude(user_id__in=busy_operator_ids)
            .order_by(
                "location__name",
                "user__last_name",
                "user__first_name",
                "user__username",
            )
        )

        free_operators = [
            {
                "settings_id": item.pk,
                "user_id": item.user.pk,
                "username": item.user.username,
                "first_name": item.user.first_name,
                "last_name": item.user.last_name,
                "full_name": item.user.get_full_name(),
                "location": {
                    "id": item.location.pk,
                    "name": item.location.name,
                },
                "purposes": [
                    {
                        "id": purpose.pk,
                        "name": purpose.name,
                        "code": purpose.code,
                    }
                    for purpose in item.purposes.all()
                ],
            }
            for item in free_operator_settings
        ]
        return JsonResponse(
            {
                "purposes": purposes,
                "locations": locations,
                "free_operators": free_operators,
                },
                status=200,
            )


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


class DashboardAPIView(APIView):
    authentication_classes = [SessionAuthentication,
                              BasicAuthentication,
                              BearerAuthentication]
    permission_classes = [IsAuthenticated]

    def get_totalTalonPurposes(self, start, end):
        totalTalonPurposes = [i.c for i in TalonPurposes.objects.annotate(
            a=FilteredRelation(
                'talon',
                condition=Q(
                    talon__created_at__gt=start,
                    talon__created_at__lt=end,
                    talon__action=TalonActions.COMPLETED
                )
            )
        ).annotate(c=Count('a')).order_by('pk')]
        return totalTalonPurposes

    def get_ratingOperatorByTalonPurposes(self, start, end):
        ans = {'data': [], 'operator': []}
        operators = OperatorSettings.objects.select_related('user').all()
        purposes = TalonPurposes.objects.values('pk', 'name').order_by('pk')
        temp_data = []
        for op in operators:
            temp = {pur.get('purpose'): pur.get('c') for pur in Talon.objects.filter(logs__action=TalonActions.COMPLETED, logs__created_by=op.user, created_at__gt=start, created_at__lt=end).values(
                'purpose').annotate(c=Count('purpose')).order_by('purpose')}
            data = [temp.get(v.get('pk'), 0) for v in purposes]
            temp_data.append(data)

        data = [[temp_data[j][i]
                 for j in range(len(temp_data))] for i in range(len(temp_data[0]))]
        for i, v in enumerate(purposes):
            ans['data'].append({'name': v.get('name'), 'data': data[i]})
        for op in operators:
            ans['operator'].append(op.user.username)
        return ans

    def get(self, request):
        user: CustomUser = request.user
        if not user.groups.contains(Group.objects.get(name="Admins")):
            return Response(status=403, data={'detail': 'Недостаточно прав'})
        tz = pytz.timezone(settings.TIME_ZONE)
        start = datetime.datetime.fromisoformat(
            (request.GET.get('start'))).astimezone(tz)
        end = datetime.datetime.fromisoformat(
            (request.GET.get('end'))).astimezone(tz)
        ans = {
            'TalonPurposes': [i.get('name') for i in TalonPurposes.objects.values('name').order_by('pk')],
            'totalTalonPurposes': self.get_totalTalonPurposes(start, end),
            'ratingOperatorByTalonPurposes': self.get_ratingOperatorByTalonPurposes(start, end)
        }
        return JsonResponse(ans, status=200)

class QueueStatisticsAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        data = get_queue_statistics(request.GET)
        return Response(data=data, status=status.HTTP_200_OK)


class OperatorDetailedStatisticsAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request, operator_id: int) -> Response:
        user = request.user

        is_admin = user.groups.filter(name="Admins").exists()
        is_self = user.pk == operator_id

        if not is_admin and not is_self:
            return Response(
                data={"detail": "Недостаточно прав"},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            data = get_operator_detailed_statistics(
                operator_id=operator_id,
                params=request.GET,
            )
        except CustomUser.DoesNotExist:
            return Response(
                data={"detail": "Оператор не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(data=data, status=status.HTTP_200_OK)

class QueueStatisticsFiltersAPIView(APIView):
    authentication_classes = [SessionAuthentication, BasicAuthentication, BearerAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        data = get_queue_statistics_filters()
        return Response(data=data, status=status.HTTP_200_OK)