"""Views for the companies app."""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from rolepermissions.checkers import has_permission
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.utils.is_api_request import is_api_request
from vendor_manager.views import BaseListView

from .forms import CompanyForm
from .models import Company


@method_decorator([has_permission_decorator("view_company")], name="dispatch")
class CompaniesView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = Company
    redirect_to = "companies"
    form_class = CompanyForm
    template_name_list = "all_companies.html"
    template_name_add = "add_company.html"
    permission_view = "view_company"
    permission_manage = "manage_company"


@method_decorator([login_required, has_permission_decorator("view_company")], name="dispatch")
class CompanyView(View):
    """View for retrieving, updating, and deleting a company."""

    @method_decorator([has_permission_decorator("view_company")])
    def get(self, request, company_id):
        """Retrieve company details."""
        company = get_object_or_404(Company, id=company_id)
        if request.GET.get("form") == "True":
            return self.__get_edit_form(request, company)
        return self.__get_details(request, company)

    @method_decorator([has_permission_decorator("view_company")])
    def __get_details(self, request, company):
        orders = company.orders.all()
        if is_api_request(request):
            return JsonResponse({"id": company.id, "name": company.name})
        return render(
            request,
            "company_details.html",
            {"company": company, "orders": orders, "manage_company": has_permission(request.user, "manage_company")},
        )

    @method_decorator([has_permission_decorator("manage_company")])
    def __get_edit_form(self, request, company):
        form = CompanyForm(instance=company)
        return render(request, "edit_company.html", {"form": form, "company": company})

    @method_decorator([has_permission_decorator("manage_company")])
    def put(self, request, company_id):
        """Update company details."""
        company = get_object_or_404(Company, id=company_id)
        return CompaniesView()._handle_form(request, company)

    @method_decorator([has_permission_decorator("manage_company")])
    def post(self, request, company_id):
        """Create a new order for the company."""
        return self.put(request, company_id)

    @method_decorator([has_permission_decorator("manage_company")])
    def delete(self, request, company_id):
        """Delete a company."""
        company = get_object_or_404(Company, id=company_id)
        company.delete()
        return JsonResponse({"message": "Company deleted successfully"})
