"""Views for the vendor_manager application."""

import json

import plotly.express as px
import plotly.io as pio
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie
from rolepermissions.checkers import has_object_permission, has_permission
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.utils.check_user_person_assignment import NoPersonAssignedToUser, check_user_person_assignment
from vendor_manager.utils.is_api_request import is_api_request


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


@csrf_protect
def logout_view(request):
    """Log out a user."""
    if request.method == "POST":
        logout(request)
        return redirect("main")
    return redirect("main")


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
        return self.__get_items(request)

    @method_decorator([has_permission_decorator(permission_view)])
    def __get_items(self, request):
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
                f"manage_{self.model.__name__.lower()}": has_permission(request.user, self.permission_manage),
            },
        )

    @method_decorator([has_permission_decorator(permission_manage)])
    def __get_add_form(self, request):
        form = self.form_class()
        return render(request, self.template_name_add, {"form": form})

    @method_decorator([has_permission_decorator(permission_manage)])
    def post(self, request):
        """Create a new item."""
        return self._handle_form(request)

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
                return redirect(self.redirect_to)
        else:
            if is_api_request(request):
                return JsonResponse({"error": "Invalid data"}, status=400)
            else:
                messages.error(request, form.errors)
                return redirect(self.redirect_to)
