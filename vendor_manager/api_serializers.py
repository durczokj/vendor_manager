"""Shared DRF serializer mixins."""

from typing import Any, TypeVar

from django.db.models import Model

_MT = TypeVar("_MT", bound=Model)


class ImmutablePkSerializerMixin:
    """Ignore the primary-key field in incoming data on update.

    Models with user-chosen primary keys (e.g. ``Person.id`` as a
    ``CharField``) render ``id`` as a writable field in ``ModelSerializer``.
    When a client PATCHes/PUTs a *different* ``id``, Django's
    ``Model.save()`` runs ``UPDATE ... WHERE id = <new>``, matches zero
    rows, and falls back to ``INSERT`` — creating a duplicate row instead
    of renaming the existing one. This mixin drops the pk from
    ``validated_data`` before delegating to the parent ``update`` so the
    original primary key is preserved.
    """

    def update(self, instance: _MT, validated_data: dict[str, Any]) -> _MT:
        """Strip the pk from ``validated_data``, then delegate to the parent."""
        pk_name = instance._meta.pk.name
        validated_data.pop(pk_name, None)
        return super().update(instance, validated_data)  # type: ignore[misc]
