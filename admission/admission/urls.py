"""
URL configuration for admission project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, re_path, path
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from strawberry.django.views import AsyncGraphQLView
from peopleQueue.schema import schema

urlpatterns = [
    re_path(r'^admin/', admin.site.urls),
    path('django-rq/', include('django_rq.urls')),
    re_path(r'^graphql', csrf_exempt(AsyncGraphQLView.as_view(
        schema=schema,
        subscriptions_enabled=True
    ))),
    re_path(r'api/', include([
        re_path(r'^v1/', include([
            re_path(r'^auth/', include('djoser.urls')),
            re_path(r'^auth/', csrf_exempt(include('djoser.urls.authtoken'))),
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
