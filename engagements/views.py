from django.http import HttpResponse
from django.template import loader
from .models import Engagement

from django.shortcuts import render, get_object_or_404

def engagements(request):
    myengagements = Engagement.objects.all()
    return render(request, 'all_engagements.html', {'myengagements': myengagements})

def engagement_details(request, id):
    engagement = get_object_or_404(Engagement, id=id)
    assignments = engagement.assignments.all()
    return render(
        request,
        'engagement_details.html',
        {'engagement': engagement, 'assignments': assignments})