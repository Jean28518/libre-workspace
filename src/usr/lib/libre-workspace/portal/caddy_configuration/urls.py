from django.urls import path
from . import views

urlpatterns = [
    path("", views.caddy_configuration, name="caddy_configuration"),
    path("/create_reverse_proxy", views.caddy_create_reverse_proxy, name="caddy_create_reverse_proxy"),
    path("/add_entry", views.caddy_configuration_add_entry, name="caddy_configuration_add_entry"),
    path("/edit_entry/<int:entry_id>", views.caddy_configuration_edit_entry, name="caddy_configuration_edit_entry"),
    path("/delete_entry/<int:entry_id>", views.caddy_configuration_delete_entry, name="caddy_configuration_delete_entry"),
]