from django.urls import path
from . import views

urlpatterns = [
    path("", views.wordpress_sites, name="wordpress_sites"),
    path("create_wordpress_instance", views.create_wordpress_instance_view, name="create_wordpress_instance"),
    # path("edit_wordpress_instance/<str:entry_id>", views.edit_wordpress_instance, name="edit_wordpress_instance"),
    path("delete_wordpress_instance/<str:entry_id>", views.delete_wordpress_instance_view, name="delete_wordpress_instance"),
    path("wordpress_instance/<str:entry_id>", views.wordpress_instance_view, name="wordpress_instance"),
    path("optimize_wordpress_instance/<str:entry_id>", views.optimize_wordpress_instance_view, name="optimize_wordpress_instance"),

]