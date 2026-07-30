"""URL Configuration for the undertakings app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.UndertakingListView.as_view(), name="undertaking-list"),
    path("create/", views.UndertakingCreateView.as_view(), name="undertaking-create"),
    path("<int:pk>/", views.UndertakingDetailView.as_view(), name="undertaking-detail"),
    path("<int:pk>/update/", views.UndertakingUpdateView.as_view(), name="undertaking-update"),
    path("<int:pk>/delete/", views.UndertakingDeleteView.as_view(), name="undertaking-delete"),
]
