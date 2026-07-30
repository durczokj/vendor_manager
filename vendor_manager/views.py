"""Views for the vendor_manager application."""

import logging

from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.db import connection
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from dashboards.summary_dashboard import SummaryDashboard
from vendor_manager.utils.check_user_person_assignment import NoPersonAssignedToUser, check_user_person_assignment

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
