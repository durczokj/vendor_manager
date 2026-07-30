"""Shared CBV base-classes for vendor_manager entity views.

P4.T3 — Replaces the BaseListView / BaseDetailView closure machinery with
standard Django generic CBVs that call .accessible_to(request.user) in
get_queryset and delegate writes to per-app services.

Satisfies: FR-36, NFR-2, NFR-3.
"""

from __future__ import annotations

import logging
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from rolepermissions.checkers import has_permission

logger = logging.getLogger(__name__)


class AccessibleQuerySetMixin:
    """Filter the queryset via Model.objects.accessible_to(request.user)."""

    def get_queryset(self) -> Any:
        """Return only objects accessible to the current user.

        Returns:
            A QuerySet filtered by the per-model accessible_to() method.
        """
        return self.model.objects.accessible_to(self.request.user)  # type: ignore[attr-defined]


class EntityListView(LoginRequiredMixin, AccessibleQuerySetMixin, ListView):
    """Base list view: renders _list.html with a Table instance.

    Subclass must set: model, table_class, page_title, create_url_name.
    Optionally override: permission_create.
    """

    template_name = "_list.html"
    table_class: type | None = None
    page_title: str = ""
    permission_create: str = ""
    create_url_name: str = ""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Build context with a Table instance and optional add_url.

        Args:
            **kwargs: Extra context keyword arguments.

        Returns:
            Context dict with table, page_title, and add_url keys.
        """
        ctx = super().get_context_data(**kwargs)
        can_add = bool(self.permission_create) and has_permission(self.request.user, self.permission_create)
        qs = self.get_queryset()
        table = self.table_class(qs, can_manage=can_add)  # type: ignore[call-arg]
        ctx.update(
            {
                "table": table,
                "page_title": self.page_title,
                "add_url": reverse(self.create_url_name) if can_add and self.create_url_name else None,
            }
        )
        return ctx


class EntityDetailView(LoginRequiredMixin, AccessibleQuerySetMixin, DetailView):
    """Base detail view: renders _detail.html with a field-spec and related tables.

    Subclass must set: model, update_url_name, delete_url_name, list_url_name.
    Optionally override: detail_fields, related_table_specs, permission_change.
    """

    template_name = "_detail.html"
    detail_fields: list[tuple[str, str]] = []
    related_table_specs: list[tuple[str, Any, type]] = []
    permission_change: str = ""
    update_url_name: str = ""
    delete_url_name: str = ""
    list_url_name: str = ""

    @staticmethod
    def _resolve_attr(obj: Any, path: str) -> Any:
        """Resolve a dot-separated attribute path on obj.

        Args:
            obj: Root object to traverse.
            path: Dot-separated attribute path, e.g. "company.name".

        Returns:
            The attribute value at the end of the path.
        """
        for part in path.split("."):
            obj = getattr(obj, part)
        return obj

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Build context with fields, related blocks, and action URLs.

        Args:
            **kwargs: Extra context keyword arguments.

        Returns:
            Context dict for _detail.html.
        """
        ctx = super().get_context_data(**kwargs)
        item = self.object  # type: ignore[attr-defined]
        can_manage = bool(self.permission_change) and has_permission(self.request.user, self.permission_change)
        fields = [(label, self._resolve_attr(item, attr)) for label, attr in self.detail_fields]
        related_blocks = [
            {
                "title": title,
                "table": tbl_cls(
                    qs_getter(item) if callable(qs_getter) else self._resolve_attr(item, qs_getter),
                    can_manage=can_manage,
                ),
            }
            for title, qs_getter, tbl_cls in self.related_table_specs
        ]
        ctx.update(
            {
                "fields": fields,
                "related_blocks": related_blocks,
                "can_manage": can_manage,
                "edit_url": reverse(self.update_url_name, kwargs={"pk": item.pk}) if self.update_url_name else "",
                "delete_url": reverse(self.delete_url_name, kwargs={"pk": item.pk}) if self.delete_url_name else "",
                "back_url": reverse(self.list_url_name) if self.list_url_name else "",
                "page_title": f"{type(item).__name__}: {item}",
            }
        )
        return ctx


class EntityCreateView(LoginRequiredMixin, CreateView):
    """Base create view: renders _form.html and saves via form.save().

    Subclass must set: model, form_class, success_url_name, list_url_name.
    Optionally override: page_title.
    """

    template_name = "_form.html"
    page_title: str = ""
    success_url_name: str = ""
    list_url_name: str = ""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Inject page_title, submit_label, cancel_url, and form_action.

        Args:
            **kwargs: Extra context keyword arguments.

        Returns:
            Context dict for _form.html.
        """
        ctx = super().get_context_data(**kwargs)
        ctx.update(
            {
                "page_title": self.page_title or f"Add {self.model.__name__}",  # type: ignore[attr-defined]
                "submit_label": "Save",
                "cancel_url": reverse(self.list_url_name) if self.list_url_name else "",
                "form_action": self.request.path,
            }
        )
        return ctx

    def get_success_url(self) -> str:
        """Redirect to the entity detail page after a successful create.

        Returns:
            The URL of the created object's detail page.
        """
        return reverse(self.success_url_name, kwargs={"pk": self.object.pk})  # type: ignore[attr-defined]


class EntityUpdateView(LoginRequiredMixin, AccessibleQuerySetMixin, UpdateView):
    """Base update view: renders _form.html and saves via form.save() (or service).

    Subclass must set: model, form_class, success_url_name.
    """

    template_name = "_form.html"
    success_url_name: str = ""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Inject page_title, submit_label, cancel_url, and form_action.

        Args:
            **kwargs: Extra context keyword arguments.

        Returns:
            Context dict for _form.html.
        """
        ctx = super().get_context_data(**kwargs)
        item = self.object  # type: ignore[attr-defined]
        ctx.update(
            {
                "page_title": f"Edit {type(item).__name__}: {item}",
                "submit_label": "Save",
                "form_action": self.request.path,
                "cancel_url": self.get_success_url(),
            }
        )
        return ctx

    def get_success_url(self) -> str:
        """Redirect to the entity detail page after a successful update.

        Returns:
            The URL of the updated object's detail page.
        """
        return reverse(self.success_url_name, kwargs={"pk": self.object.pk})  # type: ignore[attr-defined]


class EntityDeleteView(LoginRequiredMixin, AccessibleQuerySetMixin, DeleteView):
    """Base delete view: renders _confirm_delete.html, then redirects to list.

    Subclass must set: model, success_url_name.
    """

    template_name = "_confirm_delete.html"
    success_url_name: str = ""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add back_url for the cancel link on the confirmation page.

        Args:
            **kwargs: Extra context keyword arguments.

        Returns:
            Context dict for _confirm_delete.html.
        """
        ctx = super().get_context_data(**kwargs)
        ctx["back_url"] = reverse(self.success_url_name) if self.success_url_name else ""
        return ctx

    def get_success_url(self) -> str:
        """Redirect to the entity list after a successful delete.

        Returns:
            The URL of the entity list page.
        """
        return reverse(self.success_url_name)
