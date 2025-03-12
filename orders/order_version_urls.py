"""This module contains the URL patterns for the orders app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.OrderVersionsView.as_view(), name="order_versions"),
    path("<int:item_id>/", views.OrderVersionView.as_view(), name="order_version"),
]
