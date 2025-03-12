"""URLs for the leaves app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.leaves, name="leaves"),
    path("/delete/<int:leave_id>/", views.delete_leave, name="delete_leave"),
]
