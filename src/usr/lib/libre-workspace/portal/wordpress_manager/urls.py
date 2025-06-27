from django.urls import path
from . import views

urlpatterns = [
    path("", views.wordpress_sites, name="wordpress_sites"),
    path("create_wordpress_instance", views.create_wordpress_instance, name="create_wordpress_instance"),
    # path("edit_wordpress_instance/<int:entry_id>", views.edit_wordpress_instance, name="edit_wordpress_instance"),
    path("delete_wordpress_instance/<int:entry_id>", views.delete_wordpress_instance, name="delete_wordpress_instance"),
]