"""URLs for the people app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.PeopleView.as_view(), name="people"),
    path("<str:item_id>/", views.PersonView.as_view(), name="person"),
]
