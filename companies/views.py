from django.http import HttpResponse
from django.template import loader
from .models import Company
from django.shortcuts import render, get_object_or_404

def companies(request):
    mycompanies = Company.objects.all()
    return render(request, 'all_companies.html', {'mycompanies': mycompanies})

def company_details(request, id):
    company = get_object_or_404(Company, id=id)
    orders = company.orders.all()
    return render(
        request,
        'company_details.html', 
        {'company': company,
         'orders': orders})