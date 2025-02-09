from django.http import HttpResponse
from django.template import loader
from .models import Order, OrderVersion, Contract

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import login_required, permission_required
from rolepermissions.decorators import has_permission_decorator

@has_permission_decorator('view_order')
@login_required
def orders(request):
    myorders = Order.objects.all()
    return render(request, 'all_orders.html', {'myorders': myorders})

@has_permission_decorator('view_order')
@login_required
def order_details(request, id):
    order = get_object_or_404(Order, id=id)
    versions = order.versions.all()
    return render(request, 'order_details.html', {'order': order, 'versions': versions})

@has_permission_decorator('view_order')
@login_required
def version_details(request, order_id, version_number):
    version = get_object_or_404(OrderVersion, order_id=order_id, version_number=version_number)
    engagement_assignments = version.engagement_assignments.all()
    return render(
        request,
        'version_details.html',
        {'version': version, 'engagement_assignments': engagement_assignments})

@has_permission_decorator('view_order')
@login_required
def contract_details(request, id):
    contract = get_object_or_404(Contract, id=id)
    return render(request, 'contract_details.html', {'contract': contract})