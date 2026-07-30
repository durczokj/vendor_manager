"""URLs for the people app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.PersonListView.as_view(), name="person-list"),
    path("create/", views.PersonCreateView.as_view(), name="person-create"),
    path("<str:pk>/", views.PersonDetailView.as_view(), name="person-detail"),
    path("<str:pk>/update/", views.PersonUpdateView.as_view(), name="person-update"),
    path("<str:pk>/delete/", views.PersonDeleteView.as_view(), name="person-delete"),
]
