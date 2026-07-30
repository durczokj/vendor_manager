"""URL patterns for the order versions sub-resource."""

from django.urls import path

from .order_version_views import (
    OrderVersionCreateView,
    OrderVersionDeleteView,
    OrderVersionDetailView,
    OrderVersionListView,
    OrderVersionUpdateView,
)

urlpatterns = [
    path("", OrderVersionListView.as_view(), name="order-version-list"),
    path("create/", OrderVersionCreateView.as_view(), name="order-version-create"),
    path("<int:pk>/", OrderVersionDetailView.as_view(), name="order-version-detail"),
    path("<int:pk>/update/", OrderVersionUpdateView.as_view(), name="order-version-update"),
    path("<int:pk>/delete/", OrderVersionDeleteView.as_view(), name="order-version-delete"),
]
