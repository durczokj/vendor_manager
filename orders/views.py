"""Views for the orders app."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from rolepermissions.checkers import has_object_permission, has_permission
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.views import BaseListView

from .forms import OrderForm
from .models import Contract, Order, OrderVersion


@method_decorator([has_permission_decorator("view_order")], name="dispatch")
class OrdersView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = Order
    redirect_to = "orders"
    form_class = OrderForm
    template_name_list = "all_orders.html"
    template_name_add = "add_order.html"
    permission_view = "view_order"
    permission_manage = "manage_order"


@method_decorator([login_required, has_permission_decorator("view_order")], name="dispatch")
class OrderView(View):
    """View for retrieving, updating, and deleting an order."""

    @method_decorator([has_permission_decorator("view_order")])
    def get(self, request, order_id):
        """Retrieve order details."""
        order = get_object_or_404(Order, id=order_id)
        if not has_object_permission("access_order", request.user, order):
            return HttpResponseForbidden()
        if request.GET.get("form") == "True":
            return self.__get_edit_form(request, order)
        return self.__get_details(request, order)

    @method_decorator([has_permission_decorator("view_order")])
    def __get_details(self, request, order):
        versions = order.versions.all()
        return render(
            request,
            "order_details.html",
            {"order": order, "versions": versions, "manage_order": has_permission(request.user, "manage_order")},
        )

    @method_decorator([has_permission_decorator("manage_order")])
    def __get_edit_form(self, request, order):
        form = OrderForm(instance=order)
        return render(request, "edit_order.html", {"form": form, "order": order})

    @method_decorator([has_permission_decorator("manage_order")])
    def put(self, request, order_id):
        """Update order details."""
        order = get_object_or_404(Order, id=order_id)
        return OrdersView()._handle_form(request, order)

    @method_decorator([has_permission_decorator("manage_order")])
    def post(self, request, order_id):
        """Create a new order version."""
        return self.put(request, order_id)

    @method_decorator([has_permission_decorator("manage_order")])
    def delete(self, request, order_id):
        """Delete an order."""
        order = get_object_or_404(Order, id=order_id)
        order.delete()
        return JsonResponse({"message": "Order deleted successfully"})


@login_required
@has_permission_decorator("view_order")
def version_details(request, order_id, version_number):
    """View to display details of a specific order version."""
    version = get_object_or_404(OrderVersion, order_id=order_id, version_number=version_number)

    if not has_object_permission("access_order", request.user, version.order):
        return HttpResponseForbidden()

    engagement_assignments = version.engagement_assignments.all()
    engagement_assignments = [
        ea for ea in engagement_assignments if has_object_permission("access_engagement", request.user, ea.engagement)
    ]
    return render(
        request,
        "version_details.html",
        {"version": version, "engagement_assignments": engagement_assignments},
    )


@login_required
@has_permission_decorator("view_order")
def contract_details(request, id):
    """View to display details of a specific contract."""
    contract = get_object_or_404(Contract, id=id)

    if not has_object_permission("access_order", request.user, contract.order_version.order):
        return HttpResponseForbidden()

    return render(request, "contract_details.html", {"contract": contract})
