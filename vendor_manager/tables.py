"""Shared base table class for entity list views."""

from __future__ import annotations

from typing import Any

import django_tables2 as tables


class BaseEntityTable(tables.Table):
    """Base table that exposes a ``can_manage`` flag to action-column templates.

    Subclasses add data columns and an optional ``actions`` column whose
    template code gates edit/delete buttons behind ``{{ table.can_manage }}``.

    Usage::

        class CompanyTable(BaseEntityTable):
            actions = tables.TemplateColumn(
                template_code=COMPANY_ACTIONS,
                orderable=False,
                verbose_name="Actions",
            )
            class Meta:
                model = Company
                fields = ("id", "name", "email", "actions")

        table = CompanyTable(qs, can_manage=has_permission(user, "manage_company"))
    """

    def __init__(self, *args: Any, can_manage: bool = False, **kwargs: Any) -> None:
        """Initialise the table.

        Args:
            *args: Positional arguments forwarded to ``django_tables2.Table``.
            can_manage: When ``True`` the actions column renders edit/delete
                buttons; otherwise it renders nothing.
            **kwargs: Keyword arguments forwarded to ``django_tables2.Table``.
        """
        super().__init__(*args, **kwargs)
        self.can_manage = can_manage
