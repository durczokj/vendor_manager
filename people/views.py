"""Views for the people app."""

import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from rolepermissions.checkers import has_object_permission, has_permission
from rolepermissions.decorators import has_permission_decorator

from .forms import PersonForm
from .models import Person


def __is_api_request(request):
    return request.headers.get("Accept") == "application/json" or request.content_type == "application/json"


@method_decorator([login_required, has_permission_decorator("view_person")], name="dispatch")
class PeopleView(View):
    """View for listing all people and creating a new person."""

    def get(self, request):
        """List all people."""
        mypeople = [
            p
            for p in Person.objects.all().values()
            if has_object_permission("access_person", request.user, Person.objects.get(id=p["id"]))
        ]
        form = PersonForm() if has_permission(request.user, "add_person") else None
        return render(request, "all_people.html", {"mypeople": mypeople, "form": form})

    @method_decorator([csrf_exempt, has_permission_decorator("add_person")])
    def post(self, request):
        """Create a new person."""
        if __is_api_request(request):
            data = json.loads(request.body)
        else:
            data = request.POST

        form = PersonForm(data)
        form.user = request.user
        if form.is_valid():
            person = form.save()
            if __is_api_request(request):
                return JsonResponse({"id": person.id}, status=201)
            else:
                return redirect("people")
        else:
            if __is_api_request(request):
                return JsonResponse({"error": "Invalid data"}, status=400)
            else:
                messages.error(request, form.errors)
                return redirect("people")


@method_decorator(csrf_exempt, name="dispatch")
class PersonView(View):
    """View for retrieving, updating, and deleting a person."""

    def get(self, request, person_id, action=None):
        """Retrieve person details."""
        person = get_object_or_404(Person, id=person_id)
        if action == "edit":
            return self.__get_edit_form(request, person)
        return self.__get_details(request, person)

    def __get_details(self, request, person):
        engagements = person.engagements.all()
        assignments = person.get_assignments(active_only=True)
        if __is_api_request(request):
            return JsonResponse({"id": person.id, "name": person.name})
        return render(
            request, "details.html", {"person": person, "engagements": engagements, "assignments": assignments}
        )

    def __get_edit_form(self, request, person):
        form = PersonForm(instance=person)
        return render(request, "edit.html", {"form": form, "person": person})

    def put(self, request, person_id):
        """Update person details."""
        person = get_object_or_404(Person, id=person_id)
        if __is_api_request(request):
            data = json.loads(request.body)
        else:
            data = request.POST
        person.first_name = data.get("first_name", person.first_name)
        person.last_name = data.get("last_name", person.last_name)
        person.description = data.get("description", person.description)
        person.location = data.get("location", person.location)
        person.save()
        if __is_api_request(request):
            return JsonResponse({"message": "Person updated successfully"})
        else:
            return self.get(request, person_id)

    def post(self, request, person_id):
        """Create a new assignment for the person."""
        return self.put(request, person_id)

    def delete(self, request, person_id):
        """Delete a person."""
        person = get_object_or_404(Person, id=person_id)
        person.delete()
        return JsonResponse({"message": "Person deleted successfully"})
