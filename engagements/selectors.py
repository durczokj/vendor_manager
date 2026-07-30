"""Selectors for engagement cost calculations."""

import logging

import numpy as np
import pandas as pd
from django.core.exceptions import ValidationError

from engagements.models import Engagement

logger = logging.getLogger(__name__)


class CoverageOverAllocationError(ValidationError):
    """Raised when daily undertaking coverage exceeds 100%."""


def _with_cost_related_data(engagement: Engagement) -> Engagement:
    """Return the engagement with related objects prefetched for cost selectors."""
    return (
        Engagement.objects.select_related("person")
        .prefetch_related(
            "order_version_assignments__order_version",
            "person__leaves",
            "undertaking_assignments__undertaking",
        )
        .get(pk=engagement.pk)
    )


def engagement_costs(engagement: Engagement) -> list[dict]:
    """Return day-level cost rows for an engagement."""
    engagement = _with_cost_related_data(engagement)
    date_index = pd.date_range(engagement.start_date, engagement.end_date, freq="D")
    df = pd.DataFrame({"date": date_index})

    ov_ranges = [
        (assignment.order_version.start_date, assignment.order_version.end_date)
        for assignment in engagement.order_version_assignments.all()
    ]
    if not ov_ranges:
        df["cost"] = 0.0
        return df[["date", "cost"]].to_dict(orient="records")

    ov_df = pd.DataFrame(ov_ranges, columns=["ov_start", "ov_end"])
    ov_df["ov_start"] = pd.to_datetime(ov_df["ov_start"])
    ov_df["ov_end"] = pd.to_datetime(ov_df["ov_end"])

    date_matrix = date_index.values[:, None]
    ov_starts = ov_df["ov_start"].values[None, :]
    ov_ends = ov_df["ov_end"].values[None, :]
    df["active"] = ((date_matrix >= ov_starts) & (date_matrix <= ov_ends)).any(axis=1)

    leave_data = [(leave.start_date, leave.end_date, leave.percentage) for leave in engagement.person.leaves.all()]
    if not leave_data:
        df["availability"] = 1.0
    else:
        leave_df = pd.DataFrame(leave_data, columns=["l_start", "l_end", "pct"])
        leave_df["l_start"] = pd.to_datetime(leave_df["l_start"])
        leave_df["l_end"] = pd.to_datetime(leave_df["l_end"])
        leave_df["pct"] = leave_df["pct"].astype(float)

        l_starts = leave_df["l_start"].values[None, :]
        l_ends = leave_df["l_end"].values[None, :]
        l_pcts = leave_df["pct"].values[None, :]

        overlaps = (date_matrix >= l_starts) & (date_matrix <= l_ends)
        df["availability"] = np.maximum(0.0, 1.0 - (overlaps * l_pcts).sum(axis=1))

    df["cost"] = np.where(
        df["active"],
        float(engagement.daily_rate) * float(engagement.fte) * df["availability"],
        0.0,
    )
    return df[["date", "cost"]].to_dict(orient="records")


def engagement_cost_coverage(engagement: Engagement) -> list[dict]:
    """Return day-level undertaking coverage rows for an engagement."""
    engagement = _with_cost_related_data(engagement)
    date_index = pd.date_range(engagement.start_date, engagement.end_date, freq="D")

    assignments = list(engagement.undertaking_assignments.all())
    if assignments:
        ua_starts = np.array([np.datetime64(assignment.start_date) for assignment in assignments])
        ua_ends = np.array([np.datetime64(assignment.end_date) for assignment in assignments])
        ua_pcts = np.array([float(assignment.percentage) for assignment in assignments])
        ua_undertakings = [assignment.undertaking for assignment in assignments]

        date_matrix = date_index.values[:, None]
        overlaps = (date_matrix >= ua_starts[None, :]) & (date_matrix <= ua_ends[None, :])
        date_idx, ua_idx = np.where(overlaps)
        result = pd.DataFrame(
            {
                "date": date_index.values[date_idx],
                "undertaking": [ua_undertakings[index] for index in ua_idx],
                "percentage": ua_pcts[ua_idx],
            }
        )
        total_per_date = result.groupby("date")["percentage"].sum()
    else:
        result = pd.DataFrame(columns=["date", "undertaking", "percentage"])
        total_per_date = pd.Series(dtype=float)

    over = total_per_date[total_per_date > 1]
    if not over.empty:
        bad_date = over.index[0]
        raise CoverageOverAllocationError(
            f"Total coverage for engagement {engagement} on date {bad_date} is greater than 1"
        )

    ov_ranges = [
        (assignment.order_version.start_date, assignment.order_version.end_date)
        for assignment in engagement.order_version_assignments.all()
    ]
    if ov_ranges:
        ov_df = pd.DataFrame(ov_ranges, columns=["ov_start", "ov_end"])
        ov_starts = pd.to_datetime(ov_df["ov_start"]).values[None, :]
        ov_ends = pd.to_datetime(ov_df["ov_end"]).values[None, :]
        active_flags = pd.Series(
            ((date_index.values[:, None] >= ov_starts) & (date_index.values[:, None] <= ov_ends)).any(axis=1),
            index=date_index,
        )
    else:
        active_flags = pd.Series(False, index=date_index)

    total_per_date = total_per_date.reindex(date_index, fill_value=0.0)
    under_and_active = (total_per_date < 1) & active_flags
    under_dates = under_and_active[under_and_active].index

    if not under_dates.empty:
        for day in under_dates:
            logger.warning("Total coverage for engagement %s on date %s is less than 1", engagement, day.date())

        unassigned = pd.DataFrame(
            {
                "date": under_dates,
                "undertaking": None,
                "percentage": 1.0 - total_per_date[under_dates].values,
            }
        )
        result = pd.concat([result, unassigned], ignore_index=True)

    return result[["date", "undertaking", "percentage"]].to_dict(orient="records")
