"""Service layer for the dashboards app.

The public entry points are :func:`build_summary` (pre-aggregated cost series
for the dashboard) and :func:`build_cost_lines` (unaggregated day-level cost
rows for LLM / MCP / export clients). Both start from
:func:`dashboards.selectors.get_accessible_cost_rows` and share the same
role-scoping guarantees.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from typing import Any, TypedDict

from django.conf import settings
from django.contrib.auth.models import User

from dashboards.selectors import CLASS_TO_ID_COL, get_accessible_cost_rows, get_entity_name_map

VALID_CLASSES: frozenset[str] = frozenset(CLASS_TO_ID_COL.keys())
VALID_GRANULARITIES: frozenset[str] = frozenset(["Monthly", "Daily", "Total"])

# Entity classes whose display names are denormalized onto each cost line.
_NAME_CLASSES: tuple[str, ...] = ("Person", "Order", "Company", "Undertaking")


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


class CostLinesPayload(TypedDict):
    """The payload returned by :func:`build_cost_lines`."""

    date_from: str
    date_to: str
    count: int
    rows: list[dict[str, Any]]


class CostLinesSpanTooLargeError(ValueError):
    """Raised when the requested ``(date_from, date_to)`` span exceeds the cap.

    The API layer maps this to HTTP 400.
    """


def attach_display_names(user: User, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Denormalize per-entity display names onto each cost-line row in place.

    For each of ``person``, ``order``, ``company``, ``undertaking`` the row is
    given a ``<entity>_name`` key resolved via
    :func:`dashboards.selectors.get_entity_name_map`. Entities the user cannot
    access via ``accessible_to(user)`` resolve to ``None``.

    Args:
        user: The authenticated Django user; used only to scope the name
            lookups. Row-level accessibility is already enforced by
            :func:`get_accessible_cost_rows`.
        rows: The list of row dicts produced by
            :func:`get_accessible_cost_rows`.

    Returns:
        The same list, with the four ``*_name`` keys populated on every row.
    """
    ids_by_class: dict[str, set[Any]] = {}
    for class_ in _NAME_CLASSES:
        id_col = CLASS_TO_ID_COL[class_]
        ids_by_class[class_] = {r[id_col] for r in rows if r.get(id_col) is not None}

    name_maps: dict[str, dict[Any, str]] = {
        class_: get_entity_name_map(user, class_, ids) for class_, ids in ids_by_class.items()
    }

    for row in rows:
        for class_ in _NAME_CLASSES:
            id_col = CLASS_TO_ID_COL[class_]
            name_col = f"{class_.lower()}_name"
            entity_id = row.get(id_col)
            row[name_col] = name_maps[class_].get(entity_id) if entity_id is not None else None
    return rows


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
    entity_name_map = get_entity_name_map(user, class_, non_none_ids)

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


def build_cost_lines(
    user: User,
    date_range: tuple[date, date],
    entity_selection: dict[str, list[Any]],
) -> CostLinesPayload:
    """Return day-level cost rows with denormalized display names.

    The rows are the same intermediate values that :func:`build_summary`
    aggregates away — one row per ``(engagement, day)`` — with every dimension
    (person, order, company, undertaking) present on every row and the
    corresponding display names resolved through
    :func:`dashboards.selectors.get_entity_name_map`. This is the API surface
    intended for LLM / MCP / CSV export clients that need to do their own math.

    Args:
        user: The authenticated Django user. Rows are scoped to
            engagements returned by ``Engagement.objects.accessible_to(user)``.
        date_range: ``(date_from, date_to)`` — both inclusive and both
            required. The span in days must not exceed
            ``settings.DASHBOARDS_COST_LINES_MAX_DAYS``.
        entity_selection: Mapping of entity class names to lists of primary
            keys to further narrow the result. An empty list means "no
            restriction" for that class. Accessibility is already enforced by
            the initial engagement query.

    Returns:
        A :data:`CostLinesPayload` dict ready for JSON serialisation.

    Raises:
        CostLinesSpanTooLargeError: If the ``date_to - date_from`` span exceeds
            ``settings.DASHBOARDS_COST_LINES_MAX_DAYS``.
        ValueError: If ``date_from > date_to``.
    """
    date_from, date_to = date_range
    if date_from > date_to:
        raise ValueError(f"date_from ({date_from}) must not be after date_to ({date_to}).")

    max_days: int = int(getattr(settings, "DASHBOARDS_COST_LINES_MAX_DAYS", 400))
    span = (date_to - date_from) + timedelta(days=1)
    if span.days > max_days:
        raise CostLinesSpanTooLargeError(
            f"Requested span of {span.days} days exceeds the {max_days}-day cap; narrow date_from/date_to."
        )

    rows = get_accessible_cost_rows(
        user,
        min_date=date_from,
        max_date=date_to,
        entity_filters=entity_selection,
    )
    rows = attach_display_names(user, rows)

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "count": len(rows),
        "rows": rows,
    }
