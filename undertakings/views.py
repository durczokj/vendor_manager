"""Views for managing undertakings and cost centers."""

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, render
from rolepermissions.checkers import has_object_permission

from .models import CostCenter, Undertaking


@login_required
def undertakings(request):
    """View to list all undertakings accessible by the user."""
    myundertakings = Undertaking.objects.all()
    myundertakings = [u for u in myundertakings if has_object_permission("access_undertaking", request.user, u)]

    return render(request, "all_undertakings.html", {"myundertakings": myundertakings})


@login_required
def undertaking_details(request, id):
    """View to display details of a specific undertaking."""
    undertaking = get_object_or_404(Undertaking, id=id)

    if not has_object_permission("access_undertaking", request.user, undertaking):
        return HttpResponseForbidden()

    engagement_assignments = [a for a in undertaking.engagement_assignments.all()]
    return render(
        request,
        "undertaking_details.html",
        {"undertaking": undertaking, "engagement_assignments": engagement_assignments},
    )


@login_required
def cost_center_details(request, cost_center_id):
    """View to display details of a specific cost center."""
    cost_center = get_object_or_404(CostCenter, id=cost_center_id)
    return render(request, "cost_center_details.html", {"cost_center": cost_center})
