"""Views for the people app."""

from django.utils.decorators import method_decorator
from rolepermissions.decorators import has_permission_decorator

from engagements.tables import EngagementUndertakingAssignmentTable
from vendor_manager.cbv import EntityCreateView, EntityDeleteView, EntityDetailView, EntityListView, EntityUpdateView

from .forms import PersonForm
from .models import Person
from .tables import PersonTable

try:
    from engagements.tables import EngagementTable as _EngagementTable
except ImportError:  # pragma: no cover
    _EngagementTable = None


@method_decorator([has_permission_decorator("view_person")], name="dispatch")
class PersonListView(EntityListView):
    """List all people."""

    model = Person
    table_class = PersonTable
    page_title = "People"
    permission_create = "add_person"
    create_url_name = "person-create"


@method_decorator([has_permission_decorator("view_person")], name="dispatch")
class PersonDetailView(EntityDetailView):
    """Show a single person."""

    model = Person
    permission_change = "change_person"
    update_url_name = "person-update"
    delete_url_name = "person-delete"
    list_url_name = "person-list"
    detail_fields = [
        ("ID", "id"),
        ("First Name", "first_name"),
        ("Last Name", "last_name"),
        ("Description", "description"),
        ("Location", "location"),
    ]
    related_table_specs = [
        (
            "Engagements",
            lambda p: p.engagements.all(),
            _EngagementTable,
            "engagement-create",
            "add_engagement",
        ),
        (
            "Active Assignments",
            lambda p: p.get_assignments(),
            EngagementUndertakingAssignmentTable,
            "engagement-undertaking-assignment-create",
            "add_engagement_undertaking_assignment",
        ),
    ]


@method_decorator([has_permission_decorator("add_person")], name="dispatch")
class PersonCreateView(EntityCreateView):
    """Create a new person."""

    model = Person
    form_class = PersonForm
    success_url_name = "person-detail"
    list_url_name = "person-list"


@method_decorator([has_permission_decorator("change_person")], name="dispatch")
class PersonUpdateView(EntityUpdateView):
    """Edit an existing person."""

    model = Person
    form_class = PersonForm
    success_url_name = "person-detail"


@method_decorator([has_permission_decorator("delete_person")], name="dispatch")
class PersonDeleteView(EntityDeleteView):
    """Delete a person."""

    model = Person
    success_url_name = "person-list"
