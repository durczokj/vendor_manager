from django.http import HttpResponse, JsonResponse
from django.template import loader
from .models import Person
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from rolepermissions.decorators import has_permission_decorator
from rolepermissions.checkers import has_object_permission

@has_permission_decorator('view_person')
@login_required
def people(request):
    mypeople = Person.objects.all().values()
    mypeople = [p for p in mypeople if has_object_permission('access_person', request.user, Person.objects.get(id=p['id']))]

    template = loader.get_template('all_people.html')
    context = {
      'mypeople': mypeople,
    }
    return HttpResponse(template.render(context, request))

@has_permission_decorator('view_person')
@login_required
def details(request, id):
  person = Person.objects.get(id=id)

  if not has_object_permission('access_person', request.user, person):
      return HttpResponseForbidden()

  engagements = person.engagements.all()
  assignments = person.get_assignments(active_only=True)
  template = loader.get_template('details.html')
  context = {
    'person': person,
    'engagements': engagements,
    'assignments': assignments
  }
  return HttpResponse(template.render(context, request))

@has_permission_decorator('view_person')
@csrf_exempt
@login_required
def person_raw(request, id):
    try:
        person = Person.objects.get(id=id)
    except ObjectDoesNotExist:
        return JsonResponse({'error': 'Person not found'}, status=404)
    
    data = {
        'id': person.id,
        'first_name': person.first_name,
        'last_name': person.last_name,
        'description': person.description,
        'location': person.location,
    }
    return JsonResponse(data)
