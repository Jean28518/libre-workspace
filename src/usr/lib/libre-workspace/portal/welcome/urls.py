from django.urls import path

from . import views

urlpatterns = [
    path("start", views.welcome_start, name="welcome_start"),
    path("select_apps", views.welcome_select_apps, name="welcome_select_apps"),
    path("dns_settings", views.welcome_dns_settings, name="welcome_dns_settings"),
    path("libreworkspace_lite", views.libreworkspace_lite, name="libreworkspace_lite"),
    path("installation_running", views.installation_running, name="installation_running"),
    path("access", views.access, name="access"),
    path("etc_hosts", views.etc_hosts, name="etc_hosts"),
]