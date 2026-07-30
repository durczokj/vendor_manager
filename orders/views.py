"""Views for the orders app."""

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from engagements.tables import EngagementOrderVersionAssignmentTable
from vendor_manager.views import BaseDetailView, BaseListView

from .forms import CloneLatestVersionForm, OrderForm, OrderVersionForm
from .models import Order, OrderVersion
from .services import create_new_order_version
from .tables import OrderTable, OrderVersionTable

logger = logging.getLogger(__name__)


@method_decorator([has_permission_decorator("view_order")], name="dispatch")
class OrdersView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = Order
    redirect_to = "orders"
    form_class = OrderForm
    permission_view = "view_order"
    permission_manage = "manage_order"
    permission_add = "add_order"
    permission_change = "change_order"
    table_class = OrderTable
    page_title = "Orders"


@method_decorator([login_required, has_permission_decorator("view_order")], name="dispatch")
class OrderView(BaseDetailView):
    """View for retrieving, updating, and deleting a company."""

    model = Order
    form_class = OrderForm
    permission_view = "view_order"
    permission_manage = "manage_order"
    permission_change = "change_order"
    permission_delete = "delete_order"
    redirect_to = "orders"
    item_url_name = "order"
    list_url_name = "orders"
    detail_fields = [("Name", "name"), ("Company", "company")]
    related_table_specs = [
        ("Versions", lambda o: o.versions.all(), OrderVersionTable),
    ]

    def get(self, request, item_id):
        """Retrieve item details."""
        item = get_object_or_404(self.model, id=item_id)
        if request.GET.get("clone_latest_version") == "True":
            form = CloneLatestVersionForm()
            return render(
                request,
                "_form.html",
                {
                    "form": form,
                    "submit_label": "Clone",
                    "page_title": f"Clone Latest Version of Order: {item.name}",
                    "cancel_url": reverse("order", kwargs={"item_id": item.id}),
                    "form_action": (f"{reverse('order', kwargs={'item_id': item.id})}?clone_latest_version=True"),
                },
            )
        return super().get(request, item_id)

    def _handle_form(self, request, instance=None):
        """Handle form submission for creating or updating an item."""
        if request.GET.get("clone_latest_version") == "True":
            data = request.POST
            logger.debug("Cloning latest version for order: %s", instance)
            form = CloneLatestVersionForm(data)
            if form.is_valid():
                create_new_order_version(
                    order=instance,
                    contract=form.cleaned_data["contract"],
                    start_date=form.cleaned_data["start_date"],
                    end_date=form.cleaned_data["end_date"],
                    copy_engagement_assignments=form.cleaned_data["copy_engagement_assignments"],
                )
                return redirect("order", item_id=instance.id)
            else:
                messages.error(request, form.errors)
                url = f"{reverse('order', kwargs={'item_id': instance.id})}?clone_latest_version=True"
                return HttpResponseRedirect(url)
        else:
            super()._handle_form(request, instance)


@method_decorator([has_permission_decorator("view_order")], name="dispatch")
class OrderVersionsView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = OrderVersion
    redirect_to = "order_version"
    form_class = OrderVersionForm
    permission_view = "view_order"
    permission_manage = "manage_order"
    permission_add = "add_order"
    permission_change = "change_order"
    table_class = OrderVersionTable
    page_title = "Order Versions"
    add_url_name = "order_versions"


@method_decorator([login_required, has_permission_decorator("view_order")], name="dispatch")
class OrderVersionView(BaseDetailView):
    """View for retrieving, updating, and deleting a company."""

    model = OrderVersion
    form_class = OrderVersionForm
    permission_view = "view_order"
    permission_manage = "manage_order"
    permission_change = "change_order"
    permission_delete = "delete_order"
    redirect_to = "order_version"
    item_url_name = "order_version"
    list_url_name = "order_versions"
    detail_fields = [
        ("Order", "order"),
        ("Version Number", "version_number"),
        ("Contract", "contract"),
        ("Start Date", "start_date"),
        ("End Date", "end_date"),
    ]
    related_table_specs = [
        (
            "Engagement Assignments",
            lambda ov: ov.engagement_assignments.all(),
            EngagementOrderVersionAssignmentTable,
        ),
    ]
