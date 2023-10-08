from django.urls import path

from . import views

urlpatterns = [
    path("", views.unix_index, name="unix_index"),
    path("backup_settings", views.backup_settings, name="backup_settings"),
    path("retry_backup", views.retry_backup, name="retry_backup"),
    path("update_system", views.update_system, name="update_system"),
    path("reboot_system", views.reboot_system, name="reboot_system"),
    path("shutdown_system", views.shutdown_system, name="shutdown_system"),
]