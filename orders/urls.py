"""This module contains the URL patterns for the orders app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.OrdersView.as_view(), name="orders"),
    path("<int:item_id>/", views.OrderView.as_view(), name="order"),
]
