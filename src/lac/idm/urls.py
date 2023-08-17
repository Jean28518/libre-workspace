from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.user_login, name="user_login"),
    path("logout", views.user_logout, name="user_logout"),
    path("password_reset", views.user_password_reset, name="user_password_reset"),
    path("change_password", views.change_password, name="change_password"),
    path("user_settings", views.user_settings, name="user_settings"),

    path("user_administration_overview", views.user_administration_overview, name="user_administration_overview"),
]