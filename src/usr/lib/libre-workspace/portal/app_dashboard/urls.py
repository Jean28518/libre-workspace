from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    
    path("app_dashboard_entries", views.app_dashboard_entries, name="app_dashboard_entries"),
    path("new_app_dashboard_entry", views.new_app_dashboard_entry, name="new_app_dashboard_entry"),
    path("edit_app_dashboard_entry/<int:id>", views.edit_app_dashboard_entry, name="edit_app_dashboard_entry"),
    path("delete_app_dashboard_entry/<int:id>", views.delete_app_dashboard_entry, name="delete_app_dashboard_entry"),
    path("entries_json" , views.entries_json, name="entries_json"),
    path("app_dashboard_appearance" , views.app_dashboard_appearance, name="app_dashboard_appearance"),
    path("reset_app_dashboard_appearance" , views.reset_app_dashboard_appearance, name="reset_app_dashboard_appearance"),
]