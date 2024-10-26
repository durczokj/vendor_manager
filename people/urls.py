from django.urls import path
from . import views

urlpatterns = [
    path('', views.people, name='people'),
    path('details/<str:id>', views.details, name='details'),
]