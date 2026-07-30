"""URLs for the leaves app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.LeaveListView.as_view(), name="leave-list"),
    path("create/", views.LeaveCreateView.as_view(), name="leave-create"),
    path("<int:pk>/delete/", views.LeaveDeleteView.as_view(), name="leave-delete"),
]
