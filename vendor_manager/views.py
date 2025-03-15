"""Views for the vendor_manager application."""

import json

import plotly.express as px
import plotly.io as pio
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie
from rolepermissions.checkers import has_object_permission, has_permission
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.utils.check_user_person_assignment import NoPersonAssignedToUser, check_user_person_assignment
from vendor_manager.utils.is_api_request import is_api_request

def decorator(permission_name):
    """Print the permission name."""
    def print_permission_decorator(function):
        def print_permission_wrapper(*args, **kwargs):
            print(f"Permission: {permission_name}")
            return function(*args, **kwargs)
        return print_permission_wrapper
    return print_permission_decorator

@ensure_csrf_cookie
@csrf_exempt
def login_api(request):
    """Log in a user."""
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({"message": "Login successful"}, status=200)
        else:
            return JsonResponse({"error": "Invalid credentials"}, status=400)
    else:
        return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_protect
def login_web(request):
    """Render the login page and handle login logic."""
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            try:
                check_user_person_assignment(user)
            except NoPersonAssignedToUser as e:
                messages.error(request, str(e))
                return render(request, "registration/login.html")

            login(request, user)
            return redirect("main")  # Redirect to a success page.
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, "registration/login.html")


@login_required
def main(request):
    """Render the dashboard page with a sample Plotly chart."""
    user = request.user

    # Generate a sample chart
    df = px.data.iris()  # Sample data
    fig = px.scatter(df, x="sepal_width", y="sepal_length", color="species", title="Iris Dataset")
    chart_html = pio.to_html(fig, full_html=False)

    context = {"user": user, "chart": chart_html}
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
                self.permission_manage: has_permission(request.user, self.permission_manage),
            },
        )

    def __get_add_form(self, request):
        @method_decorator([has_permission_decorator(self. permission_manage)])
        def inner(self, request):
            form = self.form_class()
            return render(request, self.template_name_add, {"form": form})
        return inner(self, request)
    

    def post(self, request):
        """Create a new item."""
        @method_decorator([has_permission_decorator(self.permission_manage)])
        def inner(self, request):
            return self._handle_form(request)
        return inner(self, request)

    def _handle_form(self, request, instance=None):
        """Handle form submission for creating or updating an item."""
        if is_api_request(request):
            data = json.loads(request.body)
        else:
            data = request.POST

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


@csrf_protect
def logout_view(request):
    """Log out a user."""
    if request.method == "POST":
        logout(request)
        return redirect("main")
    return redirect("main")


@method_decorator([login_required], name="dispatch")
class BaseDetailView(View):
    """Base view for retrieving, updating, and deleting an item."""

    model = None
    form_class = None
    template_name_details = None
    template_name_edit = None
    permission_view = None
    permission_manage = None
    redirect_to = None

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
                self.permission_manage: has_permission(request.user, self.permission_manage),
            },
        )
    
    def __get_edit_form(self, request, item):
        @method_decorator([has_permission_decorator(self.permission_manage)])
        def inner(self, request, item):
            form = self.form_class(instance=item)
            return render(request, self.template_name_edit, {"form": form, "item": item})
        return inner(self, request, item)

    
    def put(self, request, item_id):
        """Update item details."""
        @method_decorator([has_permission_decorator(self.permission_manage)])
        def inner(self, request, item_id):
            item = get_object_or_404(self.model, id=item_id)
            return self._handle_form(request, item)
        return inner(self, request, item_id)

    def post(self, request, item_id):
        """Create a new related object for the item."""
        return self.put(request, item_id)
        
    def delete(self, request, item_id):
        """Delete an item."""
        @method_decorator([has_permission_decorator(self.permission_manage)])
        def inner(self, request, item_id):
            item = get_object_or_404(self.model, id=item_id)
            item.delete()
            return JsonResponse({"message": f"{self.model.__name__} deleted successfully"})
        return inner(self, request, item_id)

    def _handle_form(self, request, instance=None):
        """Handle form submission for creating or updating an item."""
        if is_api_request(request):
            data = json.loads(request.body)
        else:
            data = request.POST

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
