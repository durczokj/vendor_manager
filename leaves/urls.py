from django.urls import path
from . import views

urlpatterns = [
    path('', views.leaves, name='leaves'),
]