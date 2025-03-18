"""Models for engagements."""

import logging
from datetime import date

from django.core.exceptions import ValidationError
from django.db import models

from orders.models import Order, OrderVersion
from people.models import Person
from undertakings.models import Undertaking
from vendor_manager.utils.list_dates_between import list_dates_between


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
        costs_lst = []
        for dt in list_dates_between(self.start_date, self.end_date):
            cost = 0
            active = self.active(dt)
            if active:
                avalilability = 1
                leaves = self.person.leaves.filter(start_date__lte=dt, end_date__gte=dt)
                for leave in leaves:
                    avalilability = max(0, avalilability - leave.percentage)

                cost = float(self.daily_rate * self.fte * avalilability)

            costs_lst.append({"date": dt, "cost": cost})
        return costs_lst

    @property
    def cost_coverage(self):
        """Get the cost coverage for the engagement."""
        cost_coverage_lst = []
        for dt in list_dates_between(self.start_date, self.end_date):

            undertaking_assignments = self.undertaking_assignments.filter(start_date__lte=dt, end_date__gte=dt)

            total_coverage = 0
            for ua in undertaking_assignments:
                cost_coverage_lst.append(
                    {"date": dt, "undertaking": ua.undertaking, "percentage": float(ua.percentage)}
                )
                total_coverage += ua.percentage
            if total_coverage > 1:
                raise Exception("Total coverage for engagement %s on date %s is greater than 1" % (self, dt))
            if total_coverage < 1 and self.active(dt):
                logging.warning("Total coverage for engagement %s on date %s is less than 1" % (self, dt))
                cost_coverage_lst.append({"date": dt, "undertaking": None, "percentage": float(1 - total_coverage)})
        return cost_coverage_lst


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
