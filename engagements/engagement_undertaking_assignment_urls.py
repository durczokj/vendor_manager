"""URLs for the engagements app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.EngagementUndertakingAssignmentsView.as_view(), name="engagement_undertaking_assignments"),
    path(
        "<int:item_id>", views.EngagementUndertakingAssignmentView.as_view(), name="engagement_undertaking_assignment"
    ),
]
