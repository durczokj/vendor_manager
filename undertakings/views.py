from django.http import HttpResponse
from django.template import loader
from .models import CostCenter, Undertaking
from django.shortcuts import render, get_object_or_404

def undertakings(request):
    myundertakings = Undertaking.objects.all()
    return render(request, 'all_undertakings.html', {'myundertakings': myundertakings})

def undertaking_details(request, id):
    undertaking = get_object_or_404(Undertaking, id=id)
    assignments = [a for a in undertaking.assignments.all() if a.active]
    return render(
        request,
        'undertaking_details.html',
        {'undertaking': undertaking, 'assignments': assignments})

def cost_ceter_details(request, id):
    cost_center = get_object_or_404(CostCenter, id=id)
    return render(request, 'cost_center_details.html', {'cost_center': cost_center})
