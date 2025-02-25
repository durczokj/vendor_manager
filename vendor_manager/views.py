"""Views for the vendor_manager application."""

import json

import plotly.express as px
import plotly.io as pio
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt, csrf_protect, ensure_csrf_cookie

from vendor_manager.utils.check_user_person_assignment import NoPersonAssignedToUser, check_user_person_assignment


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
