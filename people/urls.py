"""URLs for the people app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.people, name="people"),
    path("<str:identifier>", views.details, name="person_details"),
    path("<str:identifier>/raw", views.person_raw, name="person_raw"),
]
