"""Shared CBV base-classes for vendor_manager entity views.

P4.T3 — Replaces the BaseListView / BaseDetailView closure machinery with
standard Django generic CBVs that call .accessible_to(request.user) in
get_queryset and delegate writes to per-app services.

Satisfies: FR-36, NFR-2, NFR-3.
"""

from __future__ import annotations

import datetime
import logging
from typing import Any

from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from rolepermissions.checkers import has_permission

logger = logging.getLogger(__name__)


def _apply_iso_date_widgets(form: forms.BaseForm) -> forms.BaseForm:
    """Swap DateField widgets to HTML5 date inputs with ISO format.

    Args:
        form: The form to mutate.

    Returns:
        The same form, mutated.
    """
    for field in form.fields.values():
        if isinstance(field, forms.DateField):
            field.widget = forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")
            field.input_formats = ["%Y-%m-%d"]
    return form


def _iso_format(value: Any) -> Any:
    """Return an ISO-formatted string for date/datetime; otherwise return value unchanged."""
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, datetime.date):
        return value.strftime("%Y-%m-%d")
    return value


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
    detail_fields: list[tuple] = []
    related_table_specs: list[tuple] = []
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
        fields = []
        for spec in self.detail_fields:
            # Spec is either (label, attr) or (label, attr, url_name).
            label, attr = spec[0], spec[1]
            url_name = spec[2] if len(spec) > 2 else ""
            value = self._resolve_attr(item, attr)
            url = ""
            if url_name and value is not None and hasattr(value, "pk") and value.pk is not None:
                url = reverse(url_name, kwargs={"pk": value.pk})
            fields.append({"label": label, "value": _iso_format(value), "url": url})
        related_blocks = []
        for spec in self.related_table_specs:
            # Spec is either (title, qs_getter, table_cls) or
            # (title, qs_getter, table_cls, add_url_name, add_permission) or
            # (title, qs_getter, table_cls, add_url_name, add_permission, parent_field).
            title, qs_getter, tbl_cls = spec[0], spec[1], spec[2]
            add_url_name = spec[3] if len(spec) > 3 else ""
            add_permission = spec[4] if len(spec) > 4 else ""
            parent_field = spec[5] if len(spec) > 5 else type(item).__name__.lower()
            can_add_related = bool(add_permission) and has_permission(self.request.user, add_permission)
            add_url = ""
            if can_add_related and add_url_name:
                add_url = f"{reverse(add_url_name)}?{parent_field}={item.pk}"
            related_blocks.append(
                {
                    "title": title,
                    "table": tbl_cls(
                        qs_getter(item) if callable(qs_getter) else self._resolve_attr(item, qs_getter),
                        can_manage=can_manage,
                    ),
                    "add_url": add_url,
                }
            )
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

    def get_form(self, form_class: type[forms.BaseForm] | None = None) -> forms.BaseForm:
        """Return the form with HTML5 ISO date pickers applied."""
        return _apply_iso_date_widgets(super().get_form(form_class))

    def get_initial(self) -> dict[str, Any]:
        """Seed initial form values from matching GET query params.

        Any ``?field=value`` in the request that matches a form field name is
        copied into ``initial``, enabling prepopulation when creating a child
        from a parent's detail page (e.g. ``?engagement=31``).

        Returns:
            The initial values dict for the form.
        """
        initial = super().get_initial()
        form_class = self.get_form_class()
        try:
            valid_fields = set(form_class.base_fields.keys())  # type: ignore[attr-defined]
        except AttributeError:
            valid_fields = set()
        for key, value in self.request.GET.items():
            if key in valid_fields:
                initial[key] = value
        return initial

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

    def get_form(self, form_class: type[forms.BaseForm] | None = None) -> forms.BaseForm:
        """Return the form with HTML5 ISO date pickers applied."""
        return _apply_iso_date_widgets(super().get_form(form_class))

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
