from django.http import HttpResponse
from django.template import loader
from .models import Engagement

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rolepermissions.decorators import has_permission_decorator
from rolepermissions.checkers import has_object_permission
from django.http import HttpResponseForbidden

@has_permission_decorator('view_engagement')
@login_required
def engagements(request):
    myengagements = Engagement.objects.all()
    myengagements = [e for e in myengagements if has_object_permission('access_engagement', request.user, e)]
    return render(request, 'all_engagements.html', {'myengagements': myengagements})

@has_permission_decorator('view_engagement')
@login_required
def engagement_details(request, id):
    engagement = get_object_or_404(Engagement, id=id)

    if not has_object_permission('access_engagement', request.user, engagement):
        return HttpResponseForbidden()

    assignments = engagement.undertaking_assignments.all()
    return render(
        request,
        'engagement_details.html',
        {'engagement': engagement, 'assignments': assignments})