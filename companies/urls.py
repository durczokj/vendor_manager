from django.urls import path
from . import views

urlpatterns = [
    path('', views.companies, name='companies'),
    path('<int:id>', views.company_details, name='company_details')
]