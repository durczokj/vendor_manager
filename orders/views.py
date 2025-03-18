"""Views for the orders app."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.views import BaseDetailView, BaseListView

from .forms import CloneLatestVersionForm, OrderForm, OrderVersionForm
from .models import Order, OrderVersion


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
class OrderView(BaseDetailView):
    """View for retrieving, updating, and deleting a company."""

    model = Order
    form_class = OrderForm
    template_name_details = "order_details.html"
    template_name_edit = "edit_order.html"
    permission_view = "view_order"
    permission_manage = "manage_order"
    redirect_to = "orders"

    def get_related_objects(self, order):
        """Get related objects for an order."""
        return {"versions": order.versions.all()}

    def get(self, request, item_id):
        """Retrieve item details."""
        item = get_object_or_404(self.model, id=item_id)
        if request.GET.get("clone_latest_version") == "True":
            form = CloneLatestVersionForm()
            return render(request, "clone_latest_order_version.html", {"form": form, "item": item})
        return super().get(request, item_id)

    def _handle_form(self, request, instance=None):
        """Handle form submission for creating or updating an item."""
        if request.GET.get("clone_latest_version") == "True":
            data = request.POST
            print(instance)
            form = CloneLatestVersionForm(data)
            if form.is_valid():
                instance.create_new_version(
                    form.cleaned_data["contract"],
                    form.cleaned_data["start_date"],
                    form.cleaned_data["end_date"],
                    form.cleaned_data["copy_engagement_assignments"],
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
    template_name_list = "all_order_versions.html"
    template_name_add = "add_order_version.html"
    permission_view = "view_order"
    permission_manage = "manage_order"


@method_decorator([login_required, has_permission_decorator("view_order")], name="dispatch")
class OrderVersionView(BaseDetailView):
    """View for retrieving, updating, and deleting a company."""

    model = OrderVersion
    form_class = OrderVersionForm
    template_name_details = "order_version_details.html"
    template_name_edit = "edit_order_version.html"
    permission_view = "view_order"
    permission_manage = "manage_order"
    redirect_to = "order_version"

    def get_related_objects(self, order_version):
        """Get related objects for an order."""
        return {"engagement_assignments": order_version.engagement_assignments.all()}
