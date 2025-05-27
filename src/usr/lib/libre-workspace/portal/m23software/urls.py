from django.urls import path

from . import views

urlpatterns = [
    path("client_install", views.install_client, name="m23software.install_client"),
    path("client_list", views.m23_client_list, name="m23software.client_list"),
    path("client_detail/<str:client_name>", views.m23_client_detail, name="m23software.client_detail"),
    path("client_delete/<str:client_name>", views.m23_client_delete, name="m23software.client_delete"),
]