from django.urls import path

from . import views

urlpatterns = [
    path("", views.addon_creator, name="addon_creator"),
]