"""URL Configuration for the undertakings app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.UndertakingsView.as_view(), name="undertakings"),
    path("<int:item_id>/", views.UndertakingView.as_view(), name="undertaking"),
    # path(
    #     "cost_ceter/<int:id>/",
    #     views.cost_center_details,
    #     name="cost_center_details",
    # ),
]
