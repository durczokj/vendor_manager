"""Views for the contracts app."""

from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.cbv import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView

from .forms import ContractForm
from .models import Contract
from .tables import ContractTable


@method_decorator([has_permission_decorator("view_contract")], name="dispatch")
class ContractListView(EntityListView):
    """List all contracts."""

    model = Contract
    table_class = ContractTable
    page_title = "Contracts"
    permission_create = "add_contract"
    create_url_name = "contract-create"


@method_decorator([has_permission_decorator("view_contract")], name="dispatch")
class ContractDetailView(EntityDetailView):
    """Show a single contract."""

    model = Contract
    permission_change = "change_contract"
    update_url_name = "contract-update"
    delete_url_name = "contract-delete"
    list_url_name = "contract-list"
    detail_fields = [("Name", "name"), ("Status", "status"), ("Size", "size")]


@method_decorator([has_permission_decorator("add_contract")], name="dispatch")
class ContractCreateView(EntityCreateView):
    """Create a new contract."""

    model = Contract
    form_class = ContractForm
    success_url_name = "contract-detail"
    list_url_name = "contract-list"


@method_decorator([has_permission_decorator("change_contract")], name="dispatch")
class ContractUpdateView(EntityUpdateView):
    """Edit an existing contract."""

    model = Contract
    form_class = ContractForm
    success_url_name = "contract-detail"


@method_decorator([has_permission_decorator("delete_contract")], name="dispatch")
class ContractDeleteView(EntityDeleteView):
    """Delete a contract."""

    model = Contract
    success_url_name = "contract-list"
