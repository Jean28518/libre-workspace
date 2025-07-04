from django.urls import path

from . import views

urlpatterns = [
    path("client_install", views.install_client, name="m23software.install_client"),
    path("client_list", views.m23_client_list, name="m23software.client_list"),
    path("client_detail/<str:client_name>", views.m23_client_detail, name="m23software.client_detail"),
    path("client_delete/<str:client_name>", views.m23_client_delete, name="m23software.client_delete"),
    path("client_add", views.m23_add_client, name="m23software.add_client"),

    path("group_list", views.m23_group_list, name="m23software.group_list"),
    path("group_add", views.m23_add_group, name="m23software.add_group"),
    path("group_delete/<str:group_name>", views.m23_delete_group, name="m23software.delete_group"),
    path("add_groups_to_client/<str:client_name>", views.m23_add_groups_to_client, name="m23software.add_groups_to_client"),

    path("shutdown_client/<str:client_name>", views.m23_shutdown_client, name="m23software.shutdown_client"),
    path("reboot_client/<str:client_name>", views.m23_reboot_client, name="m23software.reboot_client"),

    # path("package_manager/<str:client_name>", views.m23_package_management, name="m23software.package_management"),
    # path("package_install/<str:client_name>", views.m23_package_install, name="m23software.package_install"),
    # path("package_remove/<str:client_name>", views.m23_package_remove, name="m23software.package_remove"),
    # path("apt_package_search/<str:client_name>", views.m23_apt_package_search, name="m23software.apt_package_search"),
    # path("flatpak_package_search/<str:client_name>", views.m23_flatpak_package_search, name="m23software.flatpak_package_search"),
]