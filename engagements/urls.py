"""URLs for the engagements app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.EngagementsView.as_view(), name="engagements"),
    path("<int:item_id>", views.EngagementView.as_view(), name="engagement"),
    path(
        "<int:superitem_id>/undertaking_assignments",
        views.EngagementUndertakingAssignmentsView.as_view(),
        name="engagement_undertaking_assignments",
    ),
    path(
        "<int:superitem_id>/undertaking_assignments/<int:item_id>",
        views.EngagementUndertakingAssignmentView.as_view(),
        name="engagement_undertaking_assignment",
    ),
]
