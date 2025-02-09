"""Views for the orders app."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from rolepermissions.decorators import has_permission_decorator

from .models import Contract, Order, OrderVersion


@has_permission_decorator("view_order")
@login_required
def orders(request):
    """View to list all orders accessible by the user."""
    myorders = Order.objects.all()
    return render(request, "all_orders.html", {"myorders": myorders})


@has_permission_decorator("view_order")
@login_required
def order_details(request, identifier):
    """View to display details of a specific order."""
    order = get_object_or_404(Order, identifier=identifier)
    versions = order.versions.all()
    return render(request, "order_details.html", {"order": order, "versions": versions})


@has_permission_decorator("view_order")
@login_required
def version_details(request, order_id, version_number):
    """View to display details of a specific order version."""
    version = get_object_or_404(OrderVersion, order_id=order_id, version_number=version_number)
    engagement_assignments = version.engagement_assignments.all()
    return render(
        request,
        "version_details.html",
        {"version": version, "engagement_assignments": engagement_assignments},
    )


@has_permission_decorator("view_order")
@login_required
def contract_details(request, identifier):
    """View to display details of a specific contract."""
    contract = get_object_or_404(Contract, identifier=identifier)
    return render(request, "contract_details.html", {"contract": contract})
