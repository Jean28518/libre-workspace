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
    path("data_import_1", views.data_import_1, name="data_import_1"),
    path("data_import_2", views.data_import_2, name="data_import_2"),
    path("pick_folder", views.pick_folder, name="pick_folder"),
    path("file_explorer", views.file_explorer, name="file_explorer"),

    path("set_update_configuration", views.set_update_configuration, name="set_update_configuration"),
    
    path("send_mail", views.unix_send_mail, name="send_mail"),
]