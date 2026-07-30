"""Views for the companies app."""

from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from orders.tables import OrderTable
from vendor_manager.cbv import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView

from .forms import CompanyForm
from .models import Company
from .tables import CompanyTable


@method_decorator([has_permission_decorator("view_company")], name="dispatch")
class CompanyListView(EntityListView):
    """List all companies."""

    model = Company
    table_class = CompanyTable
    page_title = "Companies"
    permission_create = "add_company"
    create_url_name = "company-create"


@method_decorator([has_permission_decorator("view_company")], name="dispatch")
class CompanyDetailView(EntityDetailView):
    """Show a single company."""

    model = Company
    permission_change = "change_company"
    update_url_name = "company-update"
    delete_url_name = "company-delete"
    list_url_name = "company-list"
    detail_fields = [("Name", "name"), ("Email", "email")]
    related_table_specs = [
        ("Orders", lambda item: item.orders.all(), OrderTable),
    ]


@method_decorator([has_permission_decorator("add_company")], name="dispatch")
class CompanyCreateView(EntityCreateView):
    """Create a new company."""

    model = Company
    form_class = CompanyForm
    success_url_name = "company-detail"
    list_url_name = "company-list"


@method_decorator([has_permission_decorator("change_company")], name="dispatch")
class CompanyUpdateView(EntityUpdateView):
    """Edit an existing company."""

    model = Company
    form_class = CompanyForm
    success_url_name = "company-detail"


@method_decorator([has_permission_decorator("delete_company")], name="dispatch")
class CompanyDeleteView(EntityDeleteView):
    """Delete a company."""

    model = Company
    success_url_name = "company-list"
