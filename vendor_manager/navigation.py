"""Sidebar navigation registry for the vendor_manager project.

Satisfies FR-39: centralised nav registry so that adding a new entity
requires exactly one line in ``NAV_ENTRIES``.

Usage
-----
The ``nav_context_processor`` is registered in ``settings.TEMPLATES`` and
injects a ``nav`` list into every template context.  ``base.html`` iterates
over that list to render the sidebar.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from django.contrib.auth.models import User
from django.http import HttpRequest
from rolepermissions.checkers import has_permission


@dataclass
class NavEntry:
    """A single sidebar navigation entry.

    Attributes:
        label: Human-readable link text shown in the sidebar.
        url_name: Django URL name passed to ``{% url %}``.
        permission: Callable that receives a ``User`` and returns ``True``
            when that user may see this entry.  Use ``lambda u: True`` for
            entries that are always visible to authenticated users.
        icon: Optional CSS class string for an icon (e.g. a Bootstrap Icons
            class).  Not currently rendered but reserved for future use.
    """

    label: str
    url_name: str
    permission: Callable[[User], bool]
    icon: str = field(default="")


def _perm(codename: str) -> Callable[[User], bool]:
    """Return a permission callable for *codename* using rolepermissions."""

    def _check(user: User) -> bool:
        return bool(has_permission(user, codename))

    _check.__name__ = f"can_{codename}"
    return _check


#: All sidebar entries in display order.
#: To add a new entity, append exactly one ``NavEntry`` here.
NAV_ENTRIES: list[NavEntry] = [
    NavEntry(label="People", url_name="person-list", permission=_perm("view_person")),
    NavEntry(label="Companies", url_name="company-list", permission=_perm("view_company")),
    NavEntry(label="Undertakings", url_name="undertaking-list", permission=_perm("view_undertaking")),
    NavEntry(label="Engagements", url_name="engagement-list", permission=_perm("view_engagement")),
    NavEntry(label="Leaves", url_name="leave-list", permission=_perm("view_leave")),
    NavEntry(label="Contracts", url_name="contract-list", permission=_perm("view_contract")),
    NavEntry(label="Orders", url_name="order-list", permission=_perm("view_order")),
]


def nav_context_processor(request: HttpRequest) -> dict[str, list[NavEntry]]:
    """Inject ``nav`` — the filtered sidebar entries — into every template.

    Only entries whose ``permission`` callable returns ``True`` for the
    current user are included.  Unauthenticated users receive an empty list.

    Args:
        request: The current ``HttpRequest``.

    Returns:
        A dict with a single key ``"nav"`` whose value is a (possibly empty)
        list of :class:`NavEntry` instances visible to ``request.user``.
    """
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return {"nav": []}
    visible = [entry for entry in NAV_ENTRIES if entry.permission(user)]
    return {"nav": visible}
