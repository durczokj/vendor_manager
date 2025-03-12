"""Views for the contracts app."""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.views import BaseDetailView, BaseListView

from .forms import ContractForm
from .models import Contract


@method_decorator([has_permission_decorator("view_contract")], name="dispatch")
class ContractsView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = Contract
    redirect_to = "contracts"
    form_class = ContractForm
    template_name_list = "all_contracts.html"
    template_name_add = "add_contract.html"
    permission_view = "view_contract"
    permission_manage = "manage_contract"


@method_decorator([login_required, has_permission_decorator("view_contract")], name="dispatch")
class ContractView(BaseDetailView):
    """View for retrieving, updating, and deleting a contract."""

    model = Contract
    form_class = ContractForm
    template_name_details = "contract_details.html"
    template_name_edit = "edit_contract.html"
    permission_view = "view_contract"
    permission_manage = "manage_contract"
    redirect_to = "contract"
