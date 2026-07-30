"""Views for OrderVersion (split from views.py to stay < 150 lines)."""

import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from rolepermissions.decorators import has_permission_decorator

from engagements.tables import EngagementOrderVersionAssignmentTable
from vendor_manager.cbv import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView

from .forms import CloneLatestVersionForm, OrderVersionForm
from .models import Order, OrderVersion
from .services import create_new_order_version
from .tables import OrderVersionTable

logger = logging.getLogger(__name__)


@method_decorator([has_permission_decorator("view_order")], name="dispatch")
class OrderVersionListView(EntityListView):
    """List all order versions."""

    model = OrderVersion
    table_class = OrderVersionTable
    page_title = "Order Versions"
    permission_create = "add_order"
    create_url_name = "order-version-create"


@method_decorator([has_permission_decorator("view_order")], name="dispatch")
class OrderVersionDetailView(EntityDetailView):
    """Show a single order version."""

    model = OrderVersion
    permission_change = "change_order"
    update_url_name = "order-version-update"
    delete_url_name = "order-version-delete"
    list_url_name = "order-version-list"
    detail_fields = [
        ("Order", "order"),
        ("Version Number", "version_number"),
        ("Contract", "contract"),
        ("Start Date", "start_date"),
        ("End Date", "end_date"),
    ]
    related_table_specs = [
        ("Engagement Assignments", lambda ov: ov.engagement_assignments.all(), EngagementOrderVersionAssignmentTable),
    ]


@method_decorator([has_permission_decorator("add_order")], name="dispatch")
class OrderVersionCreateView(EntityCreateView):
    """Create a new order version."""

    model = OrderVersion
    form_class = OrderVersionForm
    success_url_name = "order-version-detail"
    list_url_name = "order-version-list"


@method_decorator([has_permission_decorator("change_order")], name="dispatch")
class OrderVersionUpdateView(EntityUpdateView):
    """Edit an existing order version."""

    model = OrderVersion
    form_class = OrderVersionForm
    success_url_name = "order-version-detail"


@method_decorator([has_permission_decorator("delete_order")], name="dispatch")
class OrderVersionDeleteView(EntityDeleteView):
    """Delete an order version."""

    model = OrderVersion
    success_url_name = "order-version-list"


@method_decorator([has_permission_decorator("add_order")], name="dispatch")
class OrderVersionCloneView(View):
    """Clone the latest order version via the create_new_order_version service."""

    def get(self, request, pk):
        """Show the clone form."""
        order = Order.objects.accessible_to(request.user).get(pk=pk)
        form = CloneLatestVersionForm()
        return render(
            request,
            "_form.html",
            {
                "form": form,
                "submit_label": "Clone",
                "page_title": f"Clone Latest Version of Order: {order.name}",
                "cancel_url": reverse("order-detail", kwargs={"pk": pk}),
                "form_action": request.path,
            },
        )

    def post(self, request, pk):
        """Process the clone form and call the create_new_order_version service."""
        order = Order.objects.accessible_to(request.user).get(pk=pk)
        form = CloneLatestVersionForm(request.POST)
        if form.is_valid():
            create_new_order_version(
                order=order,
                contract=form.cleaned_data["contract"],
                start_date=form.cleaned_data["start_date"],
                end_date=form.cleaned_data["end_date"],
                copy_engagement_assignments=form.cleaned_data["copy_engagement_assignments"],
            )
            return redirect("order-detail", pk=pk)
        messages.error(request, form.errors)
        return HttpResponseRedirect(request.path)
