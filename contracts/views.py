"""Views for the contracts app."""

import json

from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from rolepermissions.checkers import has_permission
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.utils.is_api_request import is_api_request
from vendor_manager.views import BaseListView

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
class ContractView(View):
    """View for retrieving, updating, and deleting a contract."""

    @method_decorator([has_permission_decorator("view_contract")])
    def get(self, request, contract_id):
        """Retrieve contract details."""
        contract = get_object_or_404(Contract, id=contract_id)
        if request.GET.get("form") == "True":
            return self.__get_edit_form(request, contract)
        return self.__get_details(request, contract)

    @method_decorator([has_permission_decorator("view_contract")])
    def __get_details(self, request, contract):
        if is_api_request(request):
            return JsonResponse({"id": contract.id, "name": contract.name})
        return render(
            request,
            "contract_details.html",
            {"contract": contract, "manage_contract": has_permission(request.user, "manage_contract")},
        )

    @method_decorator([has_permission_decorator("manage_contract")])
    def __get_edit_form(self, request, contract):
        form = ContractForm(instance=contract)
        return render(request, "edit_contract.html", {"form": form, "contract": contract})

    @method_decorator([has_permission_decorator("manage_contract")])
    def put(self, request, contract_id):
        """Update contract details."""
        contract = get_object_or_404(Contract, id=contract_id)
        if is_api_request(request):
            data = json.loads(request.body)
        else:
            data = request.POST
        for field in model_to_dict(contract).keys():
            if field in data:
                setattr(contract, field, data[field])
        contract.save()
        if is_api_request(request):
            return JsonResponse({"message": "Contract updated successfully"})
        else:
            return self.get(request, contract_id)

    @method_decorator([has_permission_decorator("manage_contract")])
    def post(self, request, contract_id):
        """Create a new order for the contract."""
        return self.put(request, contract_id)

    @method_decorator([has_permission_decorator("manage_contract")])
    def delete(self, request, contract_id):
        """Delete a contract."""
        contract = get_object_or_404(Contract, id=contract_id)
        contract.delete()
        return JsonResponse({"message": "Contract deleted successfully"})
