"""Views for the people app."""

import json

from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from rolepermissions.checkers import has_permission
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.utils.is_api_request import is_api_request
from vendor_manager.views import BaseListView

from .forms import PersonForm
from .models import Person


@method_decorator([has_permission_decorator("view_person")], name="dispatch")
class PeopleView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = Person
    redirect_to = "people"
    form_class = PersonForm
    template_name_list = "all_people.html"
    template_name_add = "add_person.html"
    permission_view = "view_person"
    permission_manage = "manage_person"


@method_decorator([login_required, has_permission_decorator("view_person")], name="dispatch")
class PersonView(View):
    """View for retrieving, updating, and deleting a person."""

    @method_decorator([has_permission_decorator("view_person")])
    def get(self, request, person_id):
        """Retrieve person details."""
        person = get_object_or_404(Person, id=person_id)
        if request.GET.get("form") == "True":
            return self.__get_edit_form(request, person)
        return self.__get_details(request, person)

    @method_decorator([has_permission_decorator("view_person")])
    def __get_details(self, request, person):
        engagements = person.engagements.all()
        assignments = person.get_assignments()
        if is_api_request(request):
            return JsonResponse({"id": person.id, "name": person.name})
        return render(
            request,
            "person_details.html",
            {
                "person": person,
                "engagements": engagements,
                "assignments": assignments,
                "manage_person": has_permission(request.user, "manage_person"),
            },
        )

    @method_decorator([has_permission_decorator("manage_person")])
    def __get_edit_form(self, request, person):
        form = PersonForm(instance=person)
        return render(request, "edit_person.html", {"form": form, "person": person})

    @method_decorator([has_permission_decorator("manage_person")])
    def put(self, request, person_id):
        """Update person details."""
        person = get_object_or_404(Person, id=person_id)
        if is_api_request(request):
            data = json.loads(request.body)
        else:
            data = request.POST
        for field in model_to_dict(person).keys():
            if field in data:
                setattr(person, field, data[field])
        person.save()
        if is_api_request(request):
            return JsonResponse({"message": "Person updated successfully"})
        else:
            return self.get(request, person_id)

    @method_decorator([has_permission_decorator("manage_person")])
    def post(self, request, person_id):
        """Create a new assignment for the person."""
        return self.put(request, person_id)

    @method_decorator([has_permission_decorator("manage_person")])
    def delete(self, request, person_id):
        """Delete a person."""
        person = get_object_or_404(Person, id=person_id)
        person.delete()
        return JsonResponse({"message": "Person deleted successfully"})
