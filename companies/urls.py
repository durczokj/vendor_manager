"""URL Configuration for the companies app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.CompaniesView.as_view(), name="companies"),
    path("<int:company_id>", views.CompanyView.as_view(), name="company"),
]
