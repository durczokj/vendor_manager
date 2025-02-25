"""URLs for the people app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.PeopleView.as_view(), name="people"),
    path("<str:person_id>/", views.PersonView.as_view(), name="person"),
    path("<str:person_id>/edit/", views.PersonView.as_view(), {"action": "edit"}, name="edit_person"),
]
