"""URL Configuration for the undertakings app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.undertakings, name="undertakings"),
    path("<int:id>/", views.undertaking_details, name="undertaking_details"),
    path(
        "cost_ceter/<int:id>/",
        views.cost_center_details,
        name="cost_center_details",
    ),
]
