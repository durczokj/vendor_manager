"""This module contains the URL patterns for the orders app."""

from django.urls import path

from . import views
from .order_version_views import OrderVersionCloneView

urlpatterns = [
    path("", views.OrderListView.as_view(), name="order-list"),
    path("create/", views.OrderCreateView.as_view(), name="order-create"),
    path("<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("<int:pk>/update/", views.OrderUpdateView.as_view(), name="order-update"),
    path("<int:pk>/delete/", views.OrderDeleteView.as_view(), name="order-delete"),
    path("<int:pk>/clone-version/", OrderVersionCloneView.as_view(), name="order-version-clone"),
]
