"""Views for the people app."""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseForbidden, JsonResponse
from django.template import loader
from django.views.decorators.csrf import csrf_exempt
from rolepermissions.checkers import has_object_permission
from rolepermissions.decorators import has_permission_decorator

from .models import Person


@has_permission_decorator("view_person")
@login_required
def people(request):
    """View to list all people accessible by the user."""
    mypeople = Person.objects.all().values()
    mypeople = [
        p
        for p in mypeople
        if has_object_permission(
            "access_person",
            request.user,
            Person.objects.get(id=p["id"]),
        )
    ]

    template = loader.get_template("all_people.html")
    context = {
        "mypeople": mypeople,
    }
    return HttpResponse(template.render(context, request))


@has_permission_decorator("view_person")
@login_required
def details(request, id):
    """View to display details of a specific person."""
    person = Person.objects.get(id=id)

    if not has_object_permission("access_person", request.user, person):
        return HttpResponseForbidden()

    engagements = person.engagements.all()
    assignments = person.get_assignments(active_only=True)
    template = loader.get_template("details.html")
    context = {"person": person, "engagements": engagements, "assignments": assignments}
    return HttpResponse(template.render(context, request))


@has_permission_decorator("view_person")
@csrf_exempt
@login_required
def person_raw(request, id):
    """Return raw data for a person."""
    try:
        person = Person.objects.get(id=id)
    except ObjectDoesNotExist:
        return JsonResponse({"error": "Person not found"}, status=404)

    data = {
        "id": person.id,
        "first_name": person.first_name,
        "last_name": person.last_name,
        "description": person.description,
        "location": person.location,
    }
    return JsonResponse(data)
