"""URL Configuration for the companies app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.ContractsView.as_view(), name="contracts"),
    path("<int:item_id>", views.ContractView.as_view(), name="contract"),
]
