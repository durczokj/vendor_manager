"""Selectors for the dashboards app.

All queries start from ``<Entity>.objects.accessible_to(user)`` so that
the returned rows never include data outside the caller's role scope.
"""

from __future__ import annotations

import logging
import math
from datetime import date
from typing import Any

import numpy as np
import pandas as pd
from django.contrib.auth.models import User

from engagements.models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment
from leaves.models import Leave

logger = logging.getLogger(__name__)

# Maps entity class names to the corresponding ID column in the cost rows dict.
CLASS_TO_ID_COL: dict[str, str] = {
    "Engagement": "engagement_id",
    "Person": "person_id",
    "Order": "order_id",
    "Company": "company_id",
    "Undertaking": "undertaking_id",
}


def _na_to_none(val: Any) -> Any:
    """Convert pandas NA / NaN sentinels to ``None`` for JSON-safe output."""
    if val is pd.NA:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    return val


def get_accessible_cost_rows(
    user: User,
    *,
    min_date: date | None = None,
    max_date: date | None = None,
    entity_filters: dict[str, list[Any]] | None = None,
) -> list[dict[str, Any]]:
    """Return day-level cost rows for all data accessible to *user*.

    The initial data set is scoped to engagements returned by
    ``Engagement.objects.accessible_to(user)``, so a *person*-role user only
    ever sees rows from their own engagements.

    Pandas and NumPy are used internally for aggregation but do **not** appear
    in the function signature or return type.

    Args:
        user: The authenticated Django user.
        min_date: Optional inclusive lower bound on the ``date`` column.
        max_date: Optional inclusive upper bound on the ``date`` column.
        entity_filters: Optional mapping of model class names (``"Person"``,
            ``"Order"``, ``"Company"``, ``"Undertaking"``, ``"Engagement"``)
            to lists of primary-key values to restrict results to.  An empty
            list for a class means "no restriction".  Accessibility is already
            enforced by the initial engagement query, so callers do not need to
            validate IDs.

    Returns:
        A list of plain-Python dicts with the following keys:

        * ``date`` – :class:`datetime.date`
        * ``cost`` – :class:`float`
        * ``engagement_id`` – :class:`int`
        * ``person_id`` – :class:`str`
        * ``order_id`` – :class:`int` or ``None``
        * ``company_id`` – :class:`int` or ``None``
        * ``undertaking_id`` – :class:`int` or ``None``
        * ``percentage`` – :class:`float` or ``None``
    """
    if entity_filters is None:
        entity_filters = {}

    # ── 1. Restrict to accessible engagements ───────────────────────────────
    eng_qs = Engagement.objects.accessible_to(user)
    eng_df = pd.DataFrame(list(eng_qs.values("id", "person_id", "start_date", "end_date", "daily_rate", "fte")))
    if eng_df.empty:
        return []

    eng_df["daily_rate"] = eng_df["daily_rate"].astype(float)
    eng_df["fte"] = eng_df["fte"].astype(float)
    eng_df["start_date"] = pd.to_datetime(eng_df["start_date"])
    eng_df["end_date"] = pd.to_datetime(eng_df["end_date"])

    accessible_eng_ids: set[int] = set(eng_df["id"])

    # ── 2. Related data scoped to accessible engagements ────────────────────
    ov_df = pd.DataFrame(
        list(
            EngagementOrderVersionAssignment.objects.filter(engagement_id__in=accessible_eng_ids).values(
                "engagement_id",
                "order_version__start_date",
                "order_version__end_date",
                "order_version__order_id",
                "order_version__order__company_id",
            )
        )
    )

    accessible_person_ids: set[Any] = set(eng_df["person_id"].unique())
    leave_df = pd.DataFrame(
        list(
            Leave.objects.filter(person_id__in=accessible_person_ids).values(
                "person_id", "start_date", "end_date", "percentage"
            )
        )
    )

    ua_df = pd.DataFrame(
        list(
            EngagementUndertakingAssignment.objects.filter(engagement_id__in=accessible_eng_ids).values(
                "engagement_id",
                "undertaking_id",
                "start_date",
                "end_date",
                "percentage",
            )
        )
    )

    # ── 3. Calendar: one row per (engagement, date) ──────────────────────────
    calendar = pd.concat(
        [
            pd.DataFrame(
                {
                    "engagement_id": row["id"],
                    "date": pd.date_range(row["start_date"], row["end_date"], freq="D"),
                }
            )
            for _, row in eng_df.iterrows()
        ],
        ignore_index=True,
    )
    calendar = calendar.merge(
        eng_df[["id", "person_id", "daily_rate", "fte"]].rename(columns={"id": "engagement_id"}),
        on="engagement_id",
    )

    # Apply date-range filters before the expensive joins
    if min_date is not None:
        calendar = calendar[calendar["date"] >= pd.Timestamp(min_date)]
    if max_date is not None:
        calendar = calendar[calendar["date"] <= pd.Timestamp(max_date)]

    if calendar.empty:
        return []

    # ── 4. Active flag (order-version date-range overlap) ───────────────────
    if not ov_df.empty:
        ov_df["order_version__start_date"] = pd.to_datetime(ov_df["order_version__start_date"])
        ov_df["order_version__end_date"] = pd.to_datetime(ov_df["order_version__end_date"])

        eng_order = (
            ov_df.groupby("engagement_id")
            .agg(
                order_id=("order_version__order_id", "first"),
                company_id=("order_version__order__company_id", "first"),
            )
            .reset_index()
        )

        cal_ov = calendar[["engagement_id", "date"]].merge(
            ov_df[["engagement_id", "order_version__start_date", "order_version__end_date"]],
            on="engagement_id",
        )
        cal_ov["covered"] = (cal_ov["date"] >= cal_ov["order_version__start_date"]) & (
            cal_ov["date"] <= cal_ov["order_version__end_date"]
        )
        active_flags = cal_ov.groupby(["engagement_id", "date"])["covered"].any().reset_index(name="active")

        calendar = calendar.merge(active_flags, on=["engagement_id", "date"], how="left")
        calendar["active"] = calendar["active"].fillna(False)
        calendar = calendar.merge(eng_order, on="engagement_id", how="left")
    else:
        calendar["active"] = False
        calendar["order_id"] = None
        calendar["company_id"] = None

    # ── 5. Leave availability ────────────────────────────────────────────────
    if not leave_df.empty:
        leave_df["start_date"] = pd.to_datetime(leave_df["start_date"])
        leave_df["end_date"] = pd.to_datetime(leave_df["end_date"])
        leave_df["percentage"] = leave_df["percentage"].astype(float)

        cal_lv = calendar[["engagement_id", "date", "person_id"]].merge(
            leave_df.rename(columns={"start_date": "l_start", "end_date": "l_end", "percentage": "l_pct"}),
            on="person_id",
        )
        cal_lv = cal_lv[(cal_lv["date"] >= cal_lv["l_start"]) & (cal_lv["date"] <= cal_lv["l_end"])]
        leave_totals = cal_lv.groupby(["engagement_id", "date"])["l_pct"].sum().reset_index(name="leave_total")

        calendar = calendar.merge(leave_totals, on=["engagement_id", "date"], how="left")
        calendar["leave_total"] = calendar["leave_total"].fillna(0.0)
        calendar["availability"] = np.maximum(0.0, 1.0 - calendar["leave_total"])
        calendar.drop(columns=["leave_total"], inplace=True)
    else:
        calendar["availability"] = 1.0

    # ── 6. Daily cost ────────────────────────────────────────────────────────
    calendar["cost"] = np.where(
        calendar["active"],
        calendar["daily_rate"] * calendar["fte"] * calendar["availability"],
        0.0,
    )

    # ── 7. Cost coverage (undertaking assignments) ───────────────────────────
    if not ua_df.empty:
        ua_df["start_date"] = pd.to_datetime(ua_df["start_date"])
        ua_df["end_date"] = pd.to_datetime(ua_df["end_date"])
        ua_df["percentage"] = ua_df["percentage"].astype(float)

        cal_ua = calendar[["engagement_id", "date"]].merge(
            ua_df.rename(columns={"start_date": "ua_start", "end_date": "ua_end", "percentage": "ua_pct"}),
            on="engagement_id",
        )
        cal_ua = cal_ua[(cal_ua["date"] >= cal_ua["ua_start"]) & (cal_ua["date"] <= cal_ua["ua_end"])]
        coverage = cal_ua[["engagement_id", "date", "undertaking_id", "ua_pct"]].rename(
            columns={"ua_pct": "percentage"}
        )

        total_per = coverage.groupby(["engagement_id", "date"])["percentage"].sum()
        total_merged = calendar[["engagement_id", "date", "active"]].merge(
            total_per.reset_index(name="total_coverage"),
            on=["engagement_id", "date"],
            how="left",
        )
        total_merged["total_coverage"] = total_merged["total_coverage"].fillna(0.0)
        under_active = total_merged[(total_merged["total_coverage"] < 1) & total_merged["active"]]

        if not under_active.empty:
            logger.warning(
                "Under-covered active dates found for %d (engagement, date) pairs",
                len(under_active),
            )
            unassigned = under_active[["engagement_id", "date"]].copy()
            unassigned["undertaking_id"] = None
            unassigned["percentage"] = 1.0 - under_active["total_coverage"].values
            coverage = pd.concat([coverage, unassigned], ignore_index=True)
    else:
        coverage = calendar.loc[calendar["active"], ["engagement_id", "date"]].copy()
        coverage["undertaking_id"] = None
        coverage["percentage"] = 1.0

    # ── 8. Merge costs × coverage ────────────────────────────────────────────
    costs_df = calendar[["engagement_id", "date", "cost", "person_id", "order_id", "company_id"]]
    full_df = costs_df.merge(coverage, on=["engagement_id", "date"], how="left")
    full_df["cost"] = (full_df["cost"] * full_df["percentage"]).fillna(0.0)
    full_df["date"] = full_df["date"].dt.date

    # ── 9. Apply entity filters within the accessible scope ──────────────────
    for class_name, ids in entity_filters.items():
        if not ids:
            continue
        col = CLASS_TO_ID_COL.get(class_name)
        if col is None:
            continue
        # Accessibility is already enforced by the initial engagement query;
        # this just narrows the result further to the requested IDs.
        full_df = full_df[full_df[col].isin(ids)]

    if full_df.empty:
        return []

    # ── 10. Serialise to plain Python ────────────────────────────────────────
    records: list[dict[str, Any]] = full_df[
        [
            "date",
            "cost",
            "engagement_id",
            "person_id",
            "order_id",
            "company_id",
            "undertaking_id",
            "percentage",
        ]
    ].to_dict(orient="records")

    return [{k: _na_to_none(v) for k, v in row.items()} for row in records]
