"""Views for the leaves app."""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rolepermissions.checkers import has_object_permission

from leaves.models import Leave


@login_required
def leaves(request):
    """View for listing all leaves."""
    myleaves = Leave.objects.all()
    myleaves = [leave for leave in myleaves if has_object_permission("access_person", request.user, leave.person)]

    return render(request, "all_leaves.html", {"myleaves": myleaves})
