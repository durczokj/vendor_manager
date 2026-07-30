"""Service layer for the dashboards app.

The public entry point is :func:`build_summary`.  It orchestrates selectors
from :mod:`dashboards.selectors` and returns a serialisable
:data:`SummaryPayload` dict.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, TypedDict

from django.contrib.auth.models import User

from companies.models import Company
from dashboards.selectors import CLASS_TO_ID_COL, get_accessible_cost_rows
from engagements.models import Engagement
from orders.models import Order
from people.models import Person
from undertakings.models import Undertaking

VALID_CLASSES: frozenset[str] = frozenset(CLASS_TO_ID_COL.keys())
VALID_GRANULARITIES: frozenset[str] = frozenset(["Monthly", "Daily", "Total"])


class SummaryRow(TypedDict):
    """A single aggregated row in the summary payload."""

    id: Any
    name: str
    cost: float
    date: str | None
    month: str | None


class SummaryPayload(TypedDict):
    """The payload returned by :func:`build_summary`."""

    class_: str
    granularity: str
    rows: list[SummaryRow]


def _get_entity_name_map(
    user: User,
    class_: str,
    entity_ids: set[Any],
) -> dict[Any, str]:
    """Return a mapping of entity PKs to display strings for *user*'s scope.

    Args:
        user: The authenticated Django user.
        class_: One of the five entity class names.
        entity_ids: The set of primary keys whose names are needed.

    Returns:
        A dict mapping each PK to a human-readable display string.
    """
    if not entity_ids:
        return {}

    if class_ == "Person":
        return {p.pk: str(p) for p in Person.objects.accessible_to(user).filter(pk__in=entity_ids)}
    if class_ == "Order":
        return {o.pk: o.name for o in Order.objects.accessible_to(user).filter(pk__in=entity_ids)}
    if class_ == "Company":
        return {c.pk: str(c) for c in Company.objects.accessible_to(user).filter(pk__in=entity_ids)}
    if class_ == "Undertaking":
        return {u.pk: str(u) for u in Undertaking.objects.accessible_to(user).filter(pk__in=entity_ids)}
    if class_ == "Engagement":
        return {e.pk: f"Engagement {e.pk}" for e in Engagement.objects.accessible_to(user).filter(pk__in=entity_ids)}
    return {}


def build_summary(
    user: User,
    class_: str,
    granularity: str,
    date_range: tuple[date | None, date | None],
    entity_selection: dict[str, list[Any]],
) -> SummaryPayload:
    """Orchestrate selectors and return a serialisable summary payload.

    Args:
        user: The authenticated Django user.  Only data accessible to this
            user is included in the result.
        class_: The entity class to group costs by.  Must be one of
            ``"Engagement"``, ``"Person"``, ``"Order"``, ``"Company"``,
            ``"Undertaking"``.
        granularity: The time bucket for aggregation.  Must be one of
            ``"Monthly"``, ``"Daily"``, ``"Total"``.
        date_range: A ``(min_date, max_date)`` tuple.  Either element may be
            ``None`` to leave the bound open.
        entity_selection: A mapping of entity class names to lists of
            primary-key values.  An empty list means "no restriction" for
            that class.

    Returns:
        A :data:`SummaryPayload` dict ready for JSON serialisation.

    Raises:
        ValueError: If ``class_`` or ``granularity`` is not a recognised value.
    """
    if class_ not in VALID_CLASSES:
        raise ValueError(f"Invalid class_: {class_!r}.  Must be one of {sorted(VALID_CLASSES)}.")
    if granularity not in VALID_GRANULARITIES:
        raise ValueError(f"Invalid granularity: {granularity!r}.  Must be one of {sorted(VALID_GRANULARITIES)}.")

    min_date, max_date = date_range

    rows = get_accessible_cost_rows(
        user,
        min_date=min_date,
        max_date=max_date,
        entity_filters=entity_selection,
    )

    id_col = CLASS_TO_ID_COL[class_]

    # Aggregate costs into (entity_id, optional time bucket) buckets.
    aggregated: dict[tuple[Any, ...], float] = defaultdict(float)
    for row in rows:
        entity_id: Any = row[id_col]
        cost: float = float(row["cost"])
        row_date: date = row["date"]

        if granularity == "Daily":
            key: tuple[Any, ...] = (entity_id, row_date.isoformat())
        elif granularity == "Monthly":
            key = (entity_id, row_date.strftime("%Y-%m"))
        else:
            key = (entity_id,)

        aggregated[key] += cost

    # Resolve display names (accessible to the user only).
    non_none_ids: set[Any] = {k[0] for k in aggregated if k[0] is not None}
    entity_name_map = _get_entity_name_map(user, class_, non_none_ids)

    output_rows: list[SummaryRow] = []
    for key, total_cost in aggregated.items():
        entity_id = key[0]
        entity_name = "(unassigned)" if entity_id is None else entity_name_map.get(entity_id, str(entity_id))

        row_out: SummaryRow = {
            "id": entity_id,
            "name": entity_name,
            "cost": total_cost,
            "date": None,
            "month": None,
        }

        if granularity == "Daily":
            row_out["date"] = key[1]
        elif granularity == "Monthly":
            row_out["month"] = key[1]

        output_rows.append(row_out)

    return {
        "class_": class_,
        "granularity": granularity,
        "rows": output_rows,
    }
