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
    path("group_detail/<str:group_name>", views.m23_group_detail, name="m23software.group_detail"),
    path("add_groups_to_client/<str:client_name>", views.m23_add_groups_to_client, name="m23software.add_groups_to_client"),
    path("remove_groups_from_client/<str:client_name>", views.m23_remove_groups_from_client, name="m23software.remove_groups_from_client"),

    path("run_bash_script/<str:entity_type>/<str:entity_name>", views.m23_run_bash_script, name="m23software.run_bash_script"),
    path("shutdown_client/<str:client_name>", views.m23_shutdown_client, name="m23software.shutdown_client"),
    path("reboot_client/<str:client_name>", views.m23_reboot_client, name="m23software.reboot_client"),
    path("add_ssh_key/<str:client_name>", views.m23_add_root_ssh_key, name="m23software.add_ssh_key"),
    path("remove_ssh_key/<str:client_name>", views.m23_remove_root_ssh_key, name="m23software.remove_ssh_key"),

    path("package_manager/<str:client_name>", views.m23_package_management, name="m23software.package_management"),
    path("package_search/<str:client_name>", views.m23_package_search, name="m23software.apt_package_search"),
    path("package_install/<str:client_name>", views.m23_package_install, name="m23software.package_install"),
    path("package_remove/<str:client_name>", views.m23_package_remove, name="m23software.package_remove"),
]