from django.http import HttpResponse
from django.template import loader
from leaves.models import Leave
from people.models import Person
from rolepermissions.checkers import has_object_permission
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

@login_required
def leaves(request):
    myleaves = Leave.objects.all()
    myleaves = [l for l in myleaves if has_object_permission('access_person', request.user, l.person)]

    return render(request, 'all_leaves.html', {'myleaves': myleaves})
