"""Views for the engagements app."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from rolepermissions.checkers import has_object_permission
from rolepermissions.decorators import has_permission_decorator

from .models import Engagement


@has_permission_decorator("view_engagement")
@login_required
def engagements(request):
    """Display all engagements the user has access to."""
    myengagements = Engagement.objects.all()
    myengagements = [e for e in myengagements if has_object_permission("access_engagement", request.user, e)]
    return render(request, "all_engagements.html", {"myengagements": myengagements})


@has_permission_decorator("view_engagement")
@login_required
def engagement_details(request, identifier):
    """Display the details of a specific engagement."""
    engagement = get_object_or_404(Engagement, identifier=identifier)

    if not has_object_permission("access_engagement", request.user, engagement):
        return HttpResponseForbidden()

    assignments = engagement.undertaking_assignments.all()
    return render(
        request,
        "engagement_details.html",
        {"engagement": engagement, "assignments": assignments},
    )
