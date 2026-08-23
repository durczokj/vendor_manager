"""URL configuration for the calendars app UI."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.CalendarAssignmentListView.as_view(), name="calendar-assignment-list"),
    path("create/", views.CalendarAssignmentCreateView.as_view(), name="calendar-assignment-create"),
    path("<int:pk>/", views.CalendarAssignmentDetailView.as_view(), name="calendar-assignment-detail"),
    path(
        "<int:pk>/update/",
        views.CalendarAssignmentUpdateView.as_view(),
        name="calendar-assignment-update",
    ),
    path(
        "<int:pk>/delete/",
        views.CalendarAssignmentDeleteView.as_view(),
        name="calendar-assignment-delete",
    ),
]
