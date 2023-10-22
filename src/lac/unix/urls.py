from django.urls import path

from . import views

urlpatterns = [
    path("", views.unix_index, name="unix_index"),
    path("backup_settings", views.backup_settings, name="backup_settings"),
    path("retry_backup", views.retry_backup, name="retry_backup"),
    path("update_system", views.update_system, name="update_system"),
    path("reboot_system", views.reboot_system, name="reboot_system"),
    path("shutdown_system", views.shutdown_system, name="shutdown_system"),

    path("data_management", views.data_management, name="data_management"),
    path("mount/<partition>", views.mount, name="mount"),
    path("umount/<partition>", views.umount, name="umount"),
    path("data_export", views.data_export, name="data_export"),
    path("abort_current_data_export", views.abort_current_data_export, name="abort_current_data_export"),
]