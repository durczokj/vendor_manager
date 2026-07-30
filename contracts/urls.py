"""URL Configuration for the contracts app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.ContractListView.as_view(), name="contract-list"),
    path("create/", views.ContractCreateView.as_view(), name="contract-create"),
    path("<int:pk>/", views.ContractDetailView.as_view(), name="contract-detail"),
    path("<int:pk>/update/", views.ContractUpdateView.as_view(), name="contract-update"),
    path("<int:pk>/delete/", views.ContractDeleteView.as_view(), name="contract-delete"),
]
