"""Views for the people app."""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from vendor_manager.views import BaseDetailView, BaseListView

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
class PersonView(BaseDetailView):
    """View for retrieving, updating, and deleting a company."""

    model = Person
    form_class = PersonForm
    template_name_details = "person_details.html"
    template_name_edit = "edit_person.html"
    permission_view = "view_person"
    permission_manage = "manage_person"
    redirect_to = "people"

    def get_related_objects(self, person):
        """Return related objects for a person."""
        return {
            "engagements": person.engagements.all(),
            "assignments": person.get_assignments(),
        }
