"""Views for the companies app."""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from orders.tables import OrderTable
from vendor_manager.views import BaseDetailView, BaseListView

from .forms import CompanyForm
from .models import Company
from .tables import CompanyTable


@method_decorator([has_permission_decorator("view_company")], name="dispatch")
class CompaniesView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = Company
    redirect_to = "companies"
    form_class = CompanyForm
    permission_view = "view_company"
    permission_manage = "manage_company"
    permission_add = "add_company"
    permission_change = "change_company"
    table_class = CompanyTable
    page_title = "Companies"


@method_decorator([login_required, has_permission_decorator("view_company")], name="dispatch")
class CompanyView(BaseDetailView):
    """View for retrieving, updating, and deleting a company."""

    model = Company
    form_class = CompanyForm
    permission_view = "view_company"
    permission_manage = "manage_company"
    permission_change = "change_company"
    permission_delete = "delete_company"
    redirect_to = "companies"
    item_url_name = "company"
    list_url_name = "companies"
    detail_fields = [("Name", "name"), ("Email", "email")]
    related_table_specs = [
        ("Orders", lambda item: item.orders.all(), OrderTable),
    ]
