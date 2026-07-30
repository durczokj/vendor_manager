"""Views for the contracts app."""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.views import BaseDetailView, BaseListView

from .forms import ContractForm
from .models import Contract
from .tables import ContractTable


@method_decorator([has_permission_decorator("view_contract")], name="dispatch")
class ContractsView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = Contract
    redirect_to = "contract"
    form_class = ContractForm
    permission_view = "view_contract"
    permission_manage = "manage_contract"
    permission_add = "add_contract"
    permission_change = "change_contract"
    table_class = ContractTable
    page_title = "Contracts"
    add_url_name = "contracts"


@method_decorator([login_required, has_permission_decorator("view_contract")], name="dispatch")
class ContractView(BaseDetailView):
    """View for retrieving, updating, and deleting a contract."""

    model = Contract
    form_class = ContractForm
    permission_view = "view_contract"
    permission_manage = "manage_contract"
    permission_change = "change_contract"
    permission_delete = "delete_contract"
    redirect_to = "contract"
    item_url_name = "contract"
    list_url_name = "contracts"
    detail_fields = [("Name", "name"), ("Status", "status"), ("Size", "size")]
