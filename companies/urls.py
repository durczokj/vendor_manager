"""URL Configuration for the companies app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.companies, name="companies"),
    path("<int:identifier>", views.company_details, name="company_details"),
]
