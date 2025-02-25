"""Views for the orders app."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from rolepermissions.checkers import has_object_permission
from rolepermissions.decorators import has_permission_decorator

from .models import Contract, Order, OrderVersion


@login_required
@has_permission_decorator("view_order")
def orders(request):
    """View to list all orders accessible by the user."""
    myorders = Order.objects.all()
    myorders = [o for o in myorders if has_object_permission("access_order", request.user, o)]
    return render(request, "all_orders.html", {"myorders": myorders})


@login_required
@has_permission_decorator("view_order")
def order_details(request, id):
    """View to display details of a specific order."""
    order = get_object_or_404(Order, id=id)

    if not has_object_permission("access_order", request.user, order):
        return HttpResponseForbidden()

    versions = order.versions.all()
    return render(request, "order_details.html", {"order": order, "versions": versions})


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
