"""This module contains the URL patterns for the orders app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.OrdersView.as_view(), name="orders"),
    path("<int:order_id>/", views.OrderView.as_view(), name="order"),
    path(
        "<int:order_id>/versions/<int:version_number>/",
        views.version_details,
        name="version_details",
    ),
]
