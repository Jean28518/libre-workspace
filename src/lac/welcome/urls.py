from django.urls import path

from . import views

urlpatterns = [
    path("index", views.welcome_index, name="welcome_index"),
    path("select_apps", views.welcome_select_apps, name="welcome_select_apps"),
    path("dns_settings", views.welcome_dns_settings, name="welcome_dns_settings"),
    path("email_settings", views.welcome_email_settings, name="welcome_email_settings"),
    path("installation_running", views.installation_running, name="installation_running"),
]