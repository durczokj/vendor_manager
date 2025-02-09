from django.http import HttpResponse
from django.template import loader
from .models import CostCenter, Undertaking
from django.shortcuts import render, get_object_or_404
from rolepermissions.checkers import has_object_permission
from django.http import HttpResponseForbidden

def undertakings(request):
    myundertakings = Undertaking.objects.all()
    myundertakings = [u for u in myundertakings if has_object_permission('access_undertaking', request.user, u)]

    return render(request, 'all_undertakings.html', {'myundertakings': myundertakings})

def undertaking_details(request, id):
    undertaking = get_object_or_404(Undertaking, id=id)

    if not has_object_permission('access_undertaking', request.user, undertaking):
        return HttpResponseForbidden()

    engagement_assignments = [a for a in undertaking.engagement_assignments.all()]
    return render(
        request,
        'undertaking_details.html',
        {'undertaking': undertaking, 'engagement_assignments': engagement_assignments})

def cost_ceter_details(request, id):
    cost_center = get_object_or_404(CostCenter, id=id)
    return render(request, 'cost_center_details.html', {'cost_center': cost_center})
