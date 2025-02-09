"""URLs for the engagements app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.engagements, name="engagements"),
    path("<int:id>", views.engagement_details, name="engagement_details"),
    # path('cost_ceter/<int:id>/', views.cost_center_details, name='cost_center_details')
]
