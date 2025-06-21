from django.urls import path
from . import views

urlpatterns = [
    path("", views.addon_center, name="addon_center"),
    path("install_addon/<str:addon_id>", views.addon_center_install_addon, name="addon_center_install_addon"),
    path("uninstall_addon/<str:addon_id>", views.addon_center_uninstall_addon, name="addon_center_uninstall_addon"),

]