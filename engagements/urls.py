"""URLs for the engagements app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.EngagementsView.as_view(), name="engagements"),
    path("<int:engagement_id>", views.EngagementView.as_view(), name="engagement"),
    # path('cost_ceter/<int:id>/', views.cost_center_details, name='cost_center_details')
]
