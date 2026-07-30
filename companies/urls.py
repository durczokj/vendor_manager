"""URL Configuration for the companies app."""

from django.urls import path

from . import views

urlpatterns = [
    path("", views.CompanyListView.as_view(), name="company-list"),
    path("create/", views.CompanyCreateView.as_view(), name="company-create"),
    path("<int:pk>/", views.CompanyDetailView.as_view(), name="company-detail"),
    path("<int:pk>/update/", views.CompanyUpdateView.as_view(), name="company-update"),
    path("<int:pk>/delete/", views.CompanyDeleteView.as_view(), name="company-delete"),
]
