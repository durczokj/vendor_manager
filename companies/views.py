"""Views for the companies app."""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.views import BaseDetailView, BaseListView

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
class CompanyView(BaseDetailView):
    """View for retrieving, updating, and deleting a company."""

    model = Company
    form_class = CompanyForm
    template_name_details = "company_details.html"
    template_name_edit = "edit_company.html"
    permission_view = "view_company"
    permission_manage = "manage_company"
    redirect_to = "companies"

    def get_related_objects(self, company):
        """Return related objects for the company."""
        return {"orders": company.orders.all()}
