"""Views for the leaves app."""

from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from rolepermissions.checkers import has_object_permission

from leaves.forms import LeaveForm
from leaves.models import Leave
from leaves.utils.leave_calendar import LeaveCalendar


@login_required
def leaves(request):
    """View for listing all leaves and adding a new leave."""
    if request.method == "POST":
        form = LeaveForm(request.POST, user=request.user)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.save()
            return redirect("leaves")  # Redirect to the same view after saving
        else:
            messages.error(request, form.errors)
    else:
        form = LeaveForm(user=request.user)

    # Get month and year from request parameters, default to current month and year
    month = int(request.GET.get("month", datetime.now().month))
    year = int(request.GET.get("year", datetime.now().year))

    # Filter leaves based on the selected month and year
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    # Filter leaves that overlap with the selected month
    myleaves = Leave.objects.filter(Q(start_date__lte=last_day) & Q(end_date__gte=first_day))
    myleaves = [leave for leave in myleaves if has_object_permission("access_person", request.user, leave.person)]

    # Generate the calendar
    calendar = LeaveCalendar(year=year, month=month, leaves=myleaves).formatmonth()

    return render(
        request,
        "all_leaves.html",
        {"myleaves": myleaves, "form": form, "calendar": calendar, "month": month, "year": year},
    )


@login_required
def delete_leave(request, leave_id):
    """View for deleting a leave."""
    leave = get_object_or_404(Leave, id=leave_id)
    if not has_object_permission("access_person", request.user, leave.person):
        return HttpResponseForbidden()
    leave.delete()
    return redirect("leaves")
