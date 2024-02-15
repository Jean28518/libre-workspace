from django.urls import path

from . import views

urlpatterns = [
    path("", views.unix_index, name="unix_index"),
    path("backup_settings", views.backup_settings, name="backup_settings"),
    path("retry_backup", views.retry_backup, name="retry_backup"),
    path("update_system", views.update_system, name="update_system"),
    path("reboot_system", views.reboot_system, name="reboot_system"),
    path("shutdown_system", views.shutdown_system, name="shutdown_system"),
    path("start_all_services", views.start_all_services, name="start_all_services"),
    path("stop_all_services", views.stop_all_services, name="stop_all_services"),

    path("data_management", views.data_management, name="data_management"),
    path("mount/<partition>", views.mount, name="mount"),
    path("umount/<partition>", views.umount, name="umount"),
    path("data_export", views.data_export, name="data_export"),
    path("abort_current_data_export", views.abort_current_data_export, name="abort_current_data_export"),
    path("data_import_1", views.data_import_1, name="data_import_1"),
    path("data_import_2", views.data_import_2, name="data_import_2"),
    path("pick_folder", views.pick_path, name="pick_folder"),
    path("file_explorer", views.file_explorer, name="file_explorer"),

    path("set_update_configuration", views.set_update_configuration, name="set_update_configuration"),

    path("system_configuration", views.system_configuration, name="system_configuration"),
    path("email_configuration", views.email_configuration, name="email_configuration"),
    path("module_management", views.module_management, name="module_management"),
    path("module_management/install/<name>", views.install_module, name="install_module"),
    path("module_management/uninstall/<name>", views.uninstall_module, name="uninstall_module"),

    path("mount_backups", views.mount_backups, name="mount_backups"),
    path("umount_backups", views.umount_backups, name="umount_backups"),
    path("recover_path", views.recover_path, name="recover_path"),
    path("enter_recovery_selector", views.enter_recovery_selector, name="enter_recovery_selector"),

    path("send_mail", views.unix_send_mail, name="send_mail"),
    path("test_mail", views.test_mail, name="test_mail"),
    
    path("addons", views.addons, name="addons"),
    path("add_addon", views.add_addon, name="add_addon"),
    path("remove_addon/<addon_id>", views.remove_addon, name="remove_addon"),
]