"""Get a DataFrame with all costs and cost coverages for all engagements."""

import logging

import numpy as np
import pandas as pd

from companies.models import Company
from engagements.models import Engagement, EngagementOrderVersionAssignment, EngagementUndertakingAssignment
from leaves.models import Leave
from orders.models import Order
from people.models import Person
from undertakings.models import Undertaking


def get_full_cost_df():
    """Returns a DataFrame with all costs and cost coverages for all engagements."""
    # === 1. Bulk fetch all raw data ===

    eng_df = pd.DataFrame(
        list(Engagement.objects.values("id", "person_id", "start_date", "end_date", "daily_rate", "fte"))
    )
    if eng_df.empty:
        return pd.DataFrame()

    eng_df["daily_rate"] = eng_df["daily_rate"].astype(float)
    eng_df["fte"] = eng_df["fte"].astype(float)
    eng_df["start_date"] = pd.to_datetime(eng_df["start_date"])
    eng_df["end_date"] = pd.to_datetime(eng_df["end_date"])

    ov_df = pd.DataFrame(
        list(
            EngagementOrderVersionAssignment.objects.values(
                "engagement_id",
                "order_version__start_date",
                "order_version__end_date",
                "order_version__order_id",
                "order_version__order__company_id",
            )
        )
    )

    leave_df = pd.DataFrame(list(Leave.objects.values("person_id", "start_date", "end_date", "percentage")))

    ua_df = pd.DataFrame(
        list(
            EngagementUndertakingAssignment.objects.values(
                "engagement_id",
                "undertaking_id",
                "start_date",
                "end_date",
                "percentage",
            )
        )
    )

    # === 2. Calendar: one row per (engagement, date) ===

    calendar = pd.concat(
        [
            pd.DataFrame(
                {"engagement_id": row["id"], "date": pd.date_range(row["start_date"], row["end_date"], freq="D")}
            )
            for _, row in eng_df.iterrows()
        ],
        ignore_index=True,
    )
    calendar = calendar.merge(
        eng_df[["id", "person_id", "daily_rate", "fte"]].rename(columns={"id": "engagement_id"}),
        on="engagement_id",
    )

    # === 3. Active flag (OV date-range overlap) ===

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

    # === 4. Leave availability ===

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

    # === 5. Cost ===

    calendar["cost"] = np.where(
        calendar["active"],
        calendar["daily_rate"] * calendar["fte"] * calendar["availability"],
        0.0,
    )

    # === 6. Cost coverage (undertaking assignments) ===

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
        over = total_per[total_per > 1]
        if not over.empty:
            eid, dt = over.index[0]
            raise Exception("Total coverage for engagement %s on date %s is greater than 1" % (eid, dt))

        total_merged = calendar[["engagement_id", "date", "active"]].merge(
            total_per.reset_index(name="total_coverage"),
            on=["engagement_id", "date"],
            how="left",
        )
        total_merged["total_coverage"] = total_merged["total_coverage"].fillna(0.0)
        under_active = total_merged[(total_merged["total_coverage"] < 1) & total_merged["active"]]

        if not under_active.empty:
            logging.warning(
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

    # === 7. Merge costs × coverage ===

    costs_df = calendar[["engagement_id", "date", "cost", "person_id", "order_id", "company_id"]]
    full_df = costs_df.merge(coverage, on=["engagement_id", "date"], how="left")
    full_df["cost"] = (full_df["cost"] * full_df["percentage"]).fillna(0.0)

    # === 8. Map IDs → Django model instances ===

    eng_map = {e.id: e for e in Engagement.objects.select_related("person")}
    order_map = {o.id: o for o in Order.objects.select_related("company")}
    person_map = {p.id: p for p in Person.objects.all()}
    company_map = {c.id: c for c in Company.objects.all()}
    undertaking_map = {u.id: u for u in Undertaking.objects.all()}

    full_df["Engagement"] = full_df["engagement_id"].map(eng_map)
    full_df["Order"] = full_df["order_id"].map(order_map)
    full_df["Person"] = full_df["person_id"].map(person_map)
    full_df["Company"] = full_df["company_id"].map(company_map)
    full_df["Undertaking"] = full_df["undertaking_id"].map(undertaking_map)

    full_df["date"] = full_df["date"].dt.date

    return full_df[["date", "cost", "Engagement", "Order", "Person", "Company", "Undertaking", "percentage"]]
