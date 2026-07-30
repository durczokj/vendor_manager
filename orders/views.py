"""Views for the orders app."""

import logging

from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.cbv import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView

from .forms import OrderForm
from .models import Order
from .tables import OrderTable, OrderVersionTable

logger = logging.getLogger(__name__)


@method_decorator([has_permission_decorator("view_order")], name="dispatch")
class OrderListView(EntityListView):
    """List all orders."""

    model = Order
    table_class = OrderTable
    page_title = "Orders"
    permission_create = "add_order"
    create_url_name = "order-create"


@method_decorator([has_permission_decorator("view_order")], name="dispatch")
class OrderDetailView(EntityDetailView):
    """Show a single order."""

    model = Order
    permission_change = "change_order"
    update_url_name = "order-update"
    delete_url_name = "order-delete"
    list_url_name = "order-list"
    detail_fields = [("Name", "name"), ("Company", "company")]
    related_table_specs = [
        ("Versions", lambda o: o.versions.all(), OrderVersionTable),
    ]


@method_decorator([has_permission_decorator("add_order")], name="dispatch")
class OrderCreateView(EntityCreateView):
    """Create a new order."""

    model = Order
    form_class = OrderForm
    success_url_name = "order-detail"
    list_url_name = "order-list"


@method_decorator([has_permission_decorator("change_order")], name="dispatch")
class OrderUpdateView(EntityUpdateView):
    """Edit an existing order."""

    model = Order
    form_class = OrderForm
    success_url_name = "order-detail"


@method_decorator([has_permission_decorator("delete_order")], name="dispatch")
class OrderDeleteView(EntityDeleteView):
    """Delete an order."""

    model = Order
    success_url_name = "order-list"
