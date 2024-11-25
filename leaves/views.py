from django.http import HttpResponse
from django.template import loader
from leaves.models import Leave

from django.shortcuts import render, get_object_or_404

def leaves(request):
    myleaves = Leave.objects.all()
    return render(request, 'all_leaves.html', {'myleaves': myleaves})
