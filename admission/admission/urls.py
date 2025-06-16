from django.conf import settings
from django.contrib import admin
from django.urls import include, re_path, path
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from strawberry.django.views import AsyncGraphQLView
from peopleQueue.schema import schema
from .middleware import WebSocketAuthMiddleware

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    path('django-rq/', include('django_rq.urls')),
    
    # HTTP GraphQL endpoint
    re_path(r'^graphql', csrf_exempt(AsyncGraphQLView.as_view(
        graphiql=settings.DEBUG,
        schema=schema,
        subscriptions_enabled=True
    ))),
    
    # API endpoints
    re_path(r'api/', include([
        re_path(r'^v1/', include([
            re_path(r'^auth/', include('djoser.urls')),
            re_path(r'^auth/', include('djoser.urls.authtoken')),
            re_path(r'^account/', include('accounts.urls')),
            re_path(r'^queue/', include('peopleQueue.urls')),
            re_path(r'^helper/', include('helper.urls')),
        ])),
        re_path(f'^schema/', include([
            path(r'', SpectacularAPIView.as_view(), name='schema'),
            re_path(r'^swagger-ui/',
                    SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        ]))
    ])),
]
