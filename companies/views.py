"""Views for the companies app."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from rolepermissions.checkers import has_object_permission

from .models import Company


@login_required
def companies(request):
    """List all companies that the user has access to."""
    mycompanies = Company.objects.all()
    mycompanies = [c for c in mycompanies if has_object_permission("access_company", request.user, c)]
    return render(request, "all_companies.html", {"mycompanies": mycompanies})


@login_required
def company_details(request, company_id):
    """Show details of a company."""
    company = get_object_or_404(Company, id=company_id)

    if not has_object_permission("access_company", request.user, company):
        return HttpResponseForbidden()

    orders = company.orders.all()
    return render(request, "company_details.html", {"company": company, "orders": orders})
