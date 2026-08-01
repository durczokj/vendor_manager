"""Models for engagements."""

from datetime import date

from django.core.exceptions import ValidationError
from django.db import models

from engagements.managers import (
    EngagementManager,
    EngagementOrderVersionAssignmentManager,
    EngagementUndertakingAssignmentManager,
)
from orders.models import Order, OrderVersion
from people.models import Person
from undertakings.models import Undertaking


class Engagement(models.Model):
    """Model for an engagement."""

    objects = EngagementManager()

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

        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

        if not (0 < self.fte <= 1):
            raise ValidationError("FTE must be between 0 and 1.")

    def save(self, *args, **kwargs):
        """Clean before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return a human-friendly summary of the engagement."""
        return f"{self.person} · {self.start_date} → {self.end_date}"


class EngagementOrderVersionAssignment(models.Model):
    """Model for the assignment of an order version to an engagement."""

    objects = EngagementOrderVersionAssignmentManager()

    engagement = models.ForeignKey(Engagement, related_name="order_version_assignments", on_delete=models.CASCADE)
    order_version = models.ForeignKey(OrderVersion, related_name="engagement_assignments", on_delete=models.CASCADE)

    class Meta:
        """Meta class for the model."""

        unique_together = (("engagement", "order_version"),)

    def clean(self):
        """Clean the class."""
        engagement_order = self.engagement.order
        if engagement_order and engagement_order != self.order_version.order:
            raise ValidationError("The engagement must belong to only one order.")

    def save(self, *args, **kwargs):
        """Clean before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return a human-friendly summary of the assignment."""
        return f"{self.engagement} → {self.order_version}"


class EngagementUndertakingAssignment(models.Model):
    """Model for the assignment of an undertaking to an engagement."""

    objects = EngagementUndertakingAssignmentManager()

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
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})
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

    def __str__(self) -> str:
        """Return a human-friendly summary of the assignment."""
        return f"{self.engagement} → {self.undertaking} ({self.percentage})"
