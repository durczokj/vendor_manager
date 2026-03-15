"""Models for engagements."""

import logging
from datetime import date

import numpy as np
import pandas as pd
from django.core.exceptions import ValidationError
from django.db import models

from orders.models import Order, OrderVersion
from people.models import Person
from undertakings.models import Undertaking


class Engagement(models.Model):
    """Model for an engagement."""

    id = models.AutoField(primary_key=True)
    person = models.ForeignKey(Person, related_name="engagements", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    fte = models.DecimalField(max_digits=3, decimal_places=2)

    def active(self, date=date.today()):
        """Check if the engagement is active."""
        return (self.start_date <= date <= self.end_date) and any(
            [a.order_version.active(date) for a in self.order_version_assignments.all()]
        )

    @property
    def order(self):
        """Get the order for the engagement."""
        orders = Order.objects.filter(
            id__in=self.order_version_assignments.values_list("order_version__order__id", flat=True)
        ).distinct()

        if len(orders) == 0:
            return None
        if len(orders) > 1:
            raise ValueError("More than one order for engagement")
        else:
            return orders.first()

    class Meta:
        """Meta class for the model."""

        unique_together = (("person", "start_date"),)

    def clean(self):
        """Clean the class."""
        super().clean()
        if not self.id:
            max_id = Engagement.objects.aggregate(models.Max("id"))["id__max"]
            self.id = (max_id or 0) + 1

        if not (0 < self.fte <= 1):
            raise ValidationError("FTE must be between 0 and 1.")

    def save(self, *args, **kwargs):
        """Clean before saving."""
        self.clean()

        # Update assignments' start and end dates
        for assignment in self.undertaking_assignments.all():
            assignment.start_date = max(self.start_date, assignment.start_date)
            assignment.end_date = min(self.end_date, assignment.end_date)
            assignment.save()

        super().save(*args, **kwargs)

    @property
    def costs(self):
        """Get the costs for the engagement."""
        # 1. Calendar of all dates
        dates = pd.date_range(self.start_date, self.end_date, freq="D")
        df = pd.DataFrame({"date": dates})

        # 2. Order version coverage → active flag (single query)
        ov_ranges = list(
            self.order_version_assignments.values_list("order_version__start_date", "order_version__end_date")
        )

        if not ov_ranges:
            df["cost"] = 0.0
            return df

        ov_df = pd.DataFrame(ov_ranges, columns=["ov_start", "ov_end"])
        ov_df["ov_start"] = pd.to_datetime(ov_df["ov_start"])
        ov_df["ov_end"] = pd.to_datetime(ov_df["ov_end"])

        dates = dates.values[:, None]  # (N, 1)
        ov_starts = ov_df["ov_start"].values[None, :]  # (1, M)
        ov_ends = ov_df["ov_end"].values[None, :]  # (1, M)
        df["active"] = ((dates >= ov_starts) & (dates <= ov_ends)).any(axis=1)

        # 3. Leave availability (single query)
        leave_data = list(self.person.leaves.values_list("start_date", "end_date", "percentage"))

        if not leave_data:
            df["availability"] = 1.0
        else:
            leave_df = pd.DataFrame(leave_data, columns=["l_start", "l_end", "pct"])
            leave_df["l_start"] = pd.to_datetime(leave_df["l_start"])
            leave_df["l_end"] = pd.to_datetime(leave_df["l_end"])
            leave_df["pct"] = leave_df["pct"].astype(float)

            l_starts = leave_df["l_start"].values[None, :]  # (1, K)
            l_ends = leave_df["l_end"].values[None, :]  # (1, K)
            l_pcts = leave_df["pct"].values[None, :]  # (1, K)

            overlaps = (dates >= l_starts) & (dates <= l_ends)  # (N, K)
            df["availability"] = np.maximum(0.0, 1.0 - (overlaps * l_pcts).sum(axis=1))

        # 4. Cost = daily_rate × fte × availability (only on active days)
        df["cost"] = np.where(
            df["active"],
            float(self.daily_rate) * float(self.fte) * df["availability"],
            0.0,
        )

        # return as a list of dicts
        return df[["date", "cost"]].to_dict(orient="records")

    @property
    def cost_coverage(self):
        """Get the cost coverage for the engagement."""
        dates = pd.date_range(self.start_date, self.end_date, freq="D")

        # 1. Fetch all undertaking assignments in one query
        ua_qs = list(self.undertaking_assignments.select_related("undertaking"))

        if ua_qs:
            ua_starts = np.array([np.datetime64(ua.start_date) for ua in ua_qs])
            ua_ends = np.array([np.datetime64(ua.end_date) for ua in ua_qs])
            ua_pcts = np.array([float(ua.percentage) for ua in ua_qs])
            ua_undertakings = [ua.undertaking for ua in ua_qs]

            # 2. Broadcasting: dates (N,1) × assignments (1,K) → overlap matrix (N,K)
            dates = dates.values[:, None]
            overlaps = (dates >= ua_starts[None, :]) & (dates <= ua_ends[None, :])

            # 3. Build rows from overlap matrix
            date_idx, ua_idx = np.where(overlaps)
            result = pd.DataFrame(
                {
                    "date": dates[date_idx],
                    "undertaking": [ua_undertakings[i] for i in ua_idx],
                    "percentage": ua_pcts[ua_idx],
                }
            )

            # 4. Validate total coverage per date
            total_per_date = result.groupby("date")["percentage"].sum()
        else:
            result = pd.DataFrame(columns=["date", "undertaking", "percentage"])
            total_per_date = pd.Series(dtype=float)

        # Check > 1
        over = total_per_date[total_per_date > 1]
        if not over.empty:
            bad_date = over.index[0]
            raise Exception("Total coverage for engagement %s on date %s is greater than 1" % (self, bad_date))

        # 5. Active flags (single query, same logic as costs)
        ov_ranges = list(
            self.order_version_assignments.values_list("order_version__start_date", "order_version__end_date")
        )
        if ov_ranges:
            ov_df = pd.DataFrame(ov_ranges, columns=["ov_start", "ov_end"])
            ov_starts = pd.to_datetime(ov_df["ov_start"]).values[None, :]
            ov_ends = pd.to_datetime(ov_df["ov_end"]).values[None, :]
            active_flags = pd.Series(
                ((dates.values[:, None] >= ov_starts) & (dates.values[:, None] <= ov_ends)).any(axis=1),
                index=dates,
            )
        else:
            active_flags = pd.Series(False, index=dates)

        # 6. Add unassigned rows where coverage < 1 and active
        total_per_date = total_per_date.reindex(dates, fill_value=0.0)
        under_and_active = (total_per_date < 1) & active_flags
        under_dates = under_and_active[under_and_active].index

        if not under_dates.empty:
            for dt in under_dates:
                logging.warning("Total coverage for engagement %s on date %s is less than 1" % (self, dt.date()))

            unassigned = pd.DataFrame(
                {
                    "date": under_dates,
                    "undertaking": None,
                    "percentage": 1.0 - total_per_date[under_dates].values,
                }
            )
            result = pd.concat([result, unassigned], ignore_index=True)

        return result[["date", "undertaking", "percentage"]].to_dict(orient="records")


class EngagementOrderVersionAssignment(models.Model):
    """Model for the assignment of an order version to an engagement."""

    engagement = models.ForeignKey(Engagement, related_name="order_version_assignments", on_delete=models.CASCADE)
    order_version = models.ForeignKey(OrderVersion, related_name="engagement_assignments", on_delete=models.CASCADE)

    class Meta:
        """Meta class for the model."""

        unique_together = (("engagement", "order_version"),)

    def clean(self):
        """Clean the class."""
        engagement_order = self.engagement.order
        if engagement_order:
            if engagement_order != self.order_version.order:
                raise ValidationError("The engagement must belong to only one order.")

    def save(self):
        """Clean before saving."""
        self.clean()
        super().save()


class EngagementUndertakingAssignment(models.Model):
    """Model for the assignment of an undertaking to an engagement."""

    engagement = models.ForeignKey(Engagement, related_name="undertaking_assignments", on_delete=models.CASCADE)
    undertaking = models.ForeignKey(Undertaking, related_name="engagement_assignments", on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    percentage = models.DecimalField(max_digits=3, decimal_places=2)

    class Meta:
        """Meta class for the model."""

        unique_together = (("engagement", "undertaking", "start_date"),)

    @property
    def active(self):
        """Check if the assignment is active."""
        return self.engagement.active

    def clean(self):
        """Clean the class."""
        super().clean()
        if self.start_date < self.engagement.start_date or self.end_date > self.engagement.end_date:
            raise ValidationError("Assignment dates must be within the engagement period.")

        overlapping_assignments = EngagementUndertakingAssignment.objects.filter(
            engagement=self.engagement,
            undertaking=self.undertaking,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date,
        ).exclude(id=self.id)
        if overlapping_assignments.exists():
            raise ValidationError("Assignments for the same engagement and undertaking cannot overlap.")

    def save(self, *args, **kwargs):
        """Clean before saving."""
        self.clean()
        super().save(*args, **kwargs)
