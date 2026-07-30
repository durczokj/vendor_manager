"""URLs for the engagements app."""

from django.urls import path

from . import views
from .order_version_assignment_views import (
    EngagementOrderVersionAssignmentCreateView,
    EngagementOrderVersionAssignmentDeleteView,
    EngagementOrderVersionAssignmentDetailView,
    EngagementOrderVersionAssignmentListView,
    EngagementOrderVersionAssignmentUpdateView,
)

urlpatterns = [
    path("", views.EngagementListView.as_view(), name="engagement-list"),
    path("create/", views.EngagementCreateView.as_view(), name="engagement-create"),
    path("<int:pk>/", views.EngagementDetailView.as_view(), name="engagement-detail"),
    path("<int:pk>/update/", views.EngagementUpdateView.as_view(), name="engagement-update"),
    path("<int:pk>/delete/", views.EngagementDeleteView.as_view(), name="engagement-delete"),
    # Undertaking assignments
    path(
        "undertaking-assignments/",
        views.EngagementUndertakingAssignmentListView.as_view(),
        name="engagement-undertaking-assignment-list",
    ),
    path(
        "undertaking-assignments/create/",
        views.EngagementUndertakingAssignmentCreateView.as_view(),
        name="engagement-undertaking-assignment-create",
    ),
    path(
        "undertaking-assignments/<int:pk>/",
        views.EngagementUndertakingAssignmentDetailView.as_view(),
        name="engagement-undertaking-assignment-detail",
    ),
    path(
        "undertaking-assignments/<int:pk>/update/",
        views.EngagementUndertakingAssignmentUpdateView.as_view(),
        name="engagement-undertaking-assignment-update",
    ),
    path(
        "undertaking-assignments/<int:pk>/delete/",
        views.EngagementUndertakingAssignmentDeleteView.as_view(),
        name="engagement-undertaking-assignment-delete",
    ),
    # Order version assignments
    path(
        "order-version-assignments/",
        EngagementOrderVersionAssignmentListView.as_view(),
        name="engagement-order-version-assignment-list",
    ),
    path(
        "order-version-assignments/create/",
        EngagementOrderVersionAssignmentCreateView.as_view(),
        name="engagement-order-version-assignment-create",
    ),
    path(
        "order-version-assignments/<int:pk>/",
        EngagementOrderVersionAssignmentDetailView.as_view(),
        name="engagement-order-version-assignment-detail",
    ),
    path(
        "order-version-assignments/<int:pk>/update/",
        EngagementOrderVersionAssignmentUpdateView.as_view(),
        name="engagement-order-version-assignment-update",
    ),
    path(
        "order-version-assignments/<int:pk>/delete/",
        EngagementOrderVersionAssignmentDeleteView.as_view(),
        name="engagement-order-version-assignment-delete",
    ),
]
