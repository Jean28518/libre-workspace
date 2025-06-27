"""lac URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import TemplateView 
from rest_framework import routers
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


from addon_center.views import AddonViewSet
from idm.views import UserViewSet, GroupViewSet

api_router = routers.DefaultRouter()

# API Endpoints:
api_router.register(r'addons', AddonViewSet, basename='addons')
api_router.register(r'users', UserViewSet, basename='users')
api_router.register(r'groups', GroupViewSet, basename='groups')


urlpatterns = [
    # API
    path('api/', include(api_router.urls)),
    path('api/auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # OpenID Connect Provider
    path('openid/', include('oidc_provider.urls', namespace='oidc_provider')),

    # Robots.txt
    path(
        "robots.txt",
        TemplateView.as_view(template_name="lac/robots.txt", content_type="text/plain"),
    ),

    # All django apps:
    path("", include("app_dashboard.urls")),
    path("addon_center/", include("addon_center.urls")),
    path("addon_creator/", include("addon_creator.urls")),
    path("caddy_configuration/", include("caddy_configuration.urls")),
    path("idm/", include("idm.urls")),
    path("m23software/", include("m23software.urls")),
    path("unix/", include("unix.urls")),
    path("welcome/", include("welcome.urls")),
    path("wordpress_manager/", include("wordpress_manager.urls")),
   
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.ADMIN_ENABLED:
    urlpatterns += [
        path("admin/", admin.site.urls),
    ]