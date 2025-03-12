"""URLs for the engagements app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.EngagementOrderVersionAssignmentsView.as_view(), name="engagement_order_version_assignments"),
    path(
        "<int:item_id>",
        views.EngagementOrderVersionAssignmentView.as_view(),
        name="engagement_order_version_assignment",
    ),
]
