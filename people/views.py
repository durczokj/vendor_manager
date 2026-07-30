"""Views for the people app."""

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from engagements.tables import EngagementUndertakingAssignmentTable
from vendor_manager.views import BaseDetailView, BaseListView

from .forms import PersonForm
from .models import Person
from .tables import PersonTable

# Lazy import to avoid circular reference: people → engagements
try:
    from engagements.tables import EngagementTable as _EngagementTable
except ImportError:  # pragma: no cover
    _EngagementTable = None


@method_decorator([has_permission_decorator("view_person")], name="dispatch")
class PeopleView(BaseListView):
    """View for listing all companies and creating a new company."""

    model = Person
    redirect_to = "people"
    form_class = PersonForm
    permission_view = "view_person"
    permission_manage = "manage_person"
    permission_add = "add_person"
    permission_change = "change_person"
    table_class = PersonTable
    page_title = "People"


@method_decorator([login_required, has_permission_decorator("view_person")], name="dispatch")
class PersonView(BaseDetailView):
    """View for retrieving, updating, and deleting a company."""

    model = Person
    form_class = PersonForm
    permission_view = "view_person"
    permission_manage = "manage_person"
    permission_change = "change_person"
    permission_delete = "delete_person"
    redirect_to = "person"
    item_url_name = "person"
    list_url_name = "people"
    detail_fields = [
        ("ID", "id"),
        ("First Name", "first_name"),
        ("Last Name", "last_name"),
        ("Description", "description"),
        ("Location", "location"),
    ]
    related_table_specs = [
        ("Engagements", lambda p: p.engagements.all(), _EngagementTable),
        (
            "Active Assignments",
            lambda p: p.get_assignments(),
            EngagementUndertakingAssignmentTable,
        ),
    ]
