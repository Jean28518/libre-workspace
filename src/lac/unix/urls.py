from django.urls import path

from . import views

urlpatterns = [
    path("", views.unix_index, name="unix_index"),
    path("backup_settings", views.backup_settings, name="backup_settings"),
    path("retry_backup", views.retry_backup, name="retry_backup"),
]