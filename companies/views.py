from django.http import HttpResponse
from django.template import loader
from .models import Company
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rolepermissions.checkers import has_object_permission
from django.http import HttpResponseForbidden

@login_required
def companies(request):
    mycompanies = Company.objects.all()
    mycompanies = [c for c in mycompanies if has_object_permission('access_company', request.user, c)]
    return render(request, 'all_companies.html', {'mycompanies': mycompanies})

@login_required
def company_details(request, id):
    company = get_object_or_404(Company, id=id)

    if not has_object_permission('access_company', request.user, company):
        return HttpResponseForbidden()

    orders = company.orders.all()
    return render(
        request,
        'company_details.html', 
        {'company': company,
         'orders': orders})