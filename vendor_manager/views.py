"""Views for the vendor_manager application."""

import logging

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.db import connection
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.static import serve as static_serve

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
    """Render the cost dashboard using the Plotly.js summary template (P5.T3)."""

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render the dashboard page.

        Args:
            request: The incoming HTTP request from an authenticated user.

        Returns:
            HTTP 200 response rendering ``dashboards/summary.html``.
        """
        return render(request=request, template_name="dashboards/summary.html")


@login_required
def serve_docs(request: HttpRequest, path: str = "") -> HttpResponseBase:
    """Serve files from the built MkDocs ``site/`` directory (FR-51, FR-54).

    Login-guarded so only authenticated users can access the documentation.
    Falls back to ``index.html`` when no path segment is provided.

    ``django.views.static.serve`` is used intentionally here — the docs
    are low-traffic internal pages and the auth wrapper cannot be satisfied
    by WhiteNoise alone.

    Args:
        request: The incoming HTTP request.
        path: The file path within the ``site/`` directory, e.g. ``architecture/``.

    Returns:
        The requested static file served from ``settings.DOCS_ROOT``, or a
        redirect to the login page if the user is not authenticated.
    """
    if not path:
        path = "index.html"
    return static_serve(request, path, document_root=settings.DOCS_ROOT)
