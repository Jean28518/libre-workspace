from django.urls import path

from . import views

urlpatterns = [
    path("dashboard", views.dashboard, name="dashboard"),
    path("login", views.user_login, name="user_login"),
    path("logout", views.user_logout, name="user_logout"),
    path("password_reset", views.user_password_reset, name="user_password_reset"),
    path("change_password", views.change_password, name="change_password"),
    path("user_settings", views.user_settings, name="user_settings"),

    path("create_totp_device", views.create_totp_device, name="create_totp_device"),
    path("delete_totp_device/<str:id>", views.delete_totp_device, name="delete_totp_device"),
    path("otp_settings", views.otp_settings, name="otp_settings"),

    path("user_overview", views.user_overview, name="user_overview"),
    path("create_user", views.create_user, name="create_user"),
    path("edit_user/<str:cn>", views.edit_user, name="edit_user"),
    path("delete_user/<str:cn>", views.delete_user, name="delete_user"),
    path("assign_groups_to_user/<str:cn>", views.assign_groups_to_user, name="assign_groups_to_user"),


    path("group_overview", views.group_overview, name="group_overview"),
    path("create_group", views.create_group, name="create_group"),
    path("edit_group/<str:cn>", views.edit_group, name="edit_group"),
    path("delete_group/<str:cn>", views.delete_group, name="delete_group"),
    path("assign_users_to_group/<str:cn>", views.assign_users_to_group, name="assign_users_to_group"),

    path("oidc_client_overview", views.oidc_client_overview, name="oidc_client_overview"),
    path("create_oidc_client", views.create_oidc_client, name="create_oidc_client"),
    path("edit_oidc_client/<str:id>", views.edit_oidc_client, name="edit_oidc_client"),
    path("delete_oidc_client/<str:id>", views.delete_oidc_client, name="delete_oidc_client"),

]