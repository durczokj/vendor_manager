"""Views for the vendor_manager application."""

import json
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.db import connection
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from rolepermissions.checkers import has_object_permission, has_permission
from rolepermissions.decorators import has_permission_decorator

from dashboards.summary_dashboard import SummaryDashboard
from vendor_manager.utils.check_user_person_assignment import NoPersonAssignedToUser, check_user_person_assignment
from vendor_manager.utils.is_api_request import is_api_request

logger = logging.getLogger(__name__)


def health(request: HttpRequest) -> HttpResponse:
    """Liveness/readiness probe target.

    Returns 200 with a plain-text body and proves DB connectivity by
    executing a trivial SELECT 1 via connection.cursor().
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok", content_type="text/plain")


class PersonLinkedLoginView(DjangoLoginView):
    """LoginView subclass that verifies the authenticated user has a linked Person.

    After credential validation, the user's Person link is checked.
    Users whose Person has been deleted or was never created are blocked
    with a non-field form error rather than being logged in.
    """

    def form_valid(self, form: AuthenticationForm) -> HttpResponse:
        """Check Person linkage before completing the login.

        Args:
            form: A validated AuthenticationForm whose get_user()
                returns the authenticated User instance.

        Returns:
            Redirect to LOGIN_REDIRECT_URL on success, or the login form
            rendered with an error if the user has no linked Person.
        """
        user = form.get_user()
        try:
            check_user_person_assignment(user)
        except NoPersonAssignedToUser as exc:
            form.add_error(None, str(exc))
            return self.form_invalid(form)
        return super().form_valid(form)


@method_decorator([login_required], name="dispatch")
class MainView(View):
    """Render the dashboard page with a sample Plotly chart."""

    dashboard = None

    def get(self, request):
        """Render the dashboard page."""
        user = request.user

        if MainView.dashboard is None:
            MainView.dashboard = SummaryDashboard()

        if request.GET.get("recalculate") == "True":
            self.dashboard.recalculate()

        form = self.dashboard.get_form(data=request.GET)
        self.dashboard.update(form)

        context = {
            "user": user,
            "form": form,
            "plot": self.dashboard.get_plot(),
            "table": self.dashboard.get_table(),
            "granularity": self.dashboard.granularity,
            "class_param_name": self.dashboard.class_param.__name__,
        }
        return render(request=request, template_name="main.html", context=context)


@method_decorator([login_required], name="dispatch")
class BaseListView(View):
    """Base view for listing items and handling forms."""

    model = None
    redirect_to = None
    form_class = None
    template_name_list = None
    template_name_add = None
    permission_view = None
    permission_manage = None
    permission_add = None
    permission_change = None

    def _get_add_permission(self):
        """Return permission codename used to guard create actions."""
        return self.permission_add or self.permission_manage

    def _get_change_permission(self):
        """Return permission codename used to guard update-related UI actions."""
        return self.permission_change or self.permission_manage

    def get(self, request):
        """List all items or show the add form."""
        if request.GET.get("form") == "True":
            return self.__get_add_form(request)
        return self.get_items(request)

    def get_items(self, request):
        """List all items."""
        items = [
            item
            for item in self.model.objects.all()
            if has_object_permission(f"access_{self.model.__name__.lower()}", request.user, item)
        ]
        return render(
            request,
            self.template_name_list,
            {
                "items": items,
                self.permission_manage: has_permission(request.user, self._get_change_permission()),
            },
        )

    def __get_add_form(self, request):
        @method_decorator([has_permission_decorator(self._get_add_permission())])
        def inner(self, request):
            form = self.form_class()
            return render(request, self.template_name_add, {"form": form})

        return inner(self, request)

    def post(self, request):
        """Create a new item."""

        @method_decorator([has_permission_decorator(self._get_add_permission())])
        def inner(self, request):
            return self._handle_form(request)

        return inner(self, request)

    def _handle_form(self, request, instance=None):
        """Handle form submission for creating or updating an item."""
        data = json.loads(request.body) if is_api_request(request) else request.POST

        form = self.form_class(data, instance=instance)
        form.user = request.user
        if form.is_valid():
            item = form.save()
            if is_api_request(request):
                return JsonResponse({"id": item.id}, status=201 if instance is None else 200)
            else:
                url = f"{reverse(self.redirect_to, kwargs={'item_id': item.id})}"
                return HttpResponseRedirect(url)
        else:
            if is_api_request(request):
                return JsonResponse({"error": "Invalid data"}, status=400)
            else:
                messages.error(request, form.errors)
                return self.__get_add_form(request)


@method_decorator([login_required], name="dispatch")
class BaseDetailView(View):
    """Base view for retrieving, updating, and deleting an item."""

    model = None
    form_class = None
    template_name_details = None
    template_name_edit = None
    permission_view = None
    permission_manage = None
    permission_change = None
    permission_delete = None
    redirect_to = None

    def _get_change_permission(self):
        """Return permission codename used to guard update actions."""
        return self.permission_change or self.permission_manage

    def _get_delete_permission(self):
        """Return permission codename used to guard delete actions."""
        return self.permission_delete or self.permission_manage

    def get(self, request, item_id):
        """Retrieve item details."""
        item = get_object_or_404(self.model, id=item_id)
        if request.GET.get("form") == "True":
            return self.__get_edit_form(request, item)
        return self.__get_details(request, item)

    def __get_details(self, request, item):
        related_objects = self.get_related_objects(item)
        if is_api_request(request):
            return JsonResponse({"id": item.id, "name": item.name})
        return render(
            request,
            self.template_name_details,
            {
                "item": item,
                "related_objects": related_objects,
                self.permission_manage: has_permission(request.user, self._get_change_permission()),
            },
        )

    def __get_edit_form(self, request, item):
        @method_decorator([has_permission_decorator(self._get_change_permission())])
        def inner(self, request, item):
            form = self.form_class(instance=item)
            return render(request, self.template_name_edit, {"form": form, "item": item})

        return inner(self, request, item)

    def put(self, request, item_id):
        """Update item details."""

        @method_decorator([has_permission_decorator(self._get_change_permission())])
        def inner(self, request, item_id):
            item = get_object_or_404(self.model, id=item_id)
            return self._handle_form(request, item)

        return inner(self, request, item_id)

    def post(self, request, item_id):
        """Create a new related object for the item."""
        return self.put(request, item_id)

    def delete(self, request, item_id):
        """Delete an item."""

        @method_decorator([has_permission_decorator(self._get_delete_permission())])
        def inner(self, request, item_id):
            item = get_object_or_404(self.model, id=item_id)
            item.delete()
            return JsonResponse({"message": f"{self.model.__name__} deleted successfully"})

        return inner(self, request, item_id)

    def _handle_form(self, request, instance=None):
        """Handle form submission for creating or updating an item."""
        data = json.loads(request.body) if is_api_request(request) else request.POST

        form = self.form_class(data, instance=instance)
        form.user = request.user
        if form.is_valid():
            item = form.save()
            if is_api_request(request):
                return JsonResponse({"id": item.id}, status=201 if instance is None else 200)
            else:
                url = f"{reverse(self.redirect_to, kwargs={'item_id': instance.id})}"
                return HttpResponseRedirect(url)
        else:
            if is_api_request(request):
                return JsonResponse({"error": "Invalid data"}, status=400)
            else:
                messages.error(request, form.errors)
                url = f"{reverse(self.redirect_to, kwargs={'item_id': instance.id})}?form=True"
                return HttpResponseRedirect(url)

    def get_related_objects(self, item):
        """Get related objects for the item. Should be overridden in subclasses."""
        return {}
