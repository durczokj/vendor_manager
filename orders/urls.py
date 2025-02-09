"""This module contains the URL patterns for the orders app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.orders, name="orders"),
    path("<int:identifier>/", views.order_details, name="order_details"),
    path(
        "<int:order_id>/versions/<int:version_number>/",
        views.version_details,
        name="version_details",
    ),
    path("contract/<int:identifier>/", views.contract_details, name="contract_details"),
]
