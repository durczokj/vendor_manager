"""Define Order and OrderVersion models."""

from datetime import date, timedelta
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models

from companies.models import Company
from contracts.models import Contract
from orders.managers import OrderManager, OrderVersionManager


class Order(models.Model):
    """Define Order model."""

    objects = OrderManager()

    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, related_name="orders", on_delete=models.CASCADE)

    def __str__(self) -> str:
        """Return the name of the order."""
        return self.name

    def create_new_version(
        self,
        contract: Contract,
        start_date: date,
        end_date: date,
        copy_engagement_assignments: bool = True,
    ) -> "OrderVersion":
        """Create a new version of the order.

        Deprecated: use orders.services.create_new_order_version directly.
        """
        from orders.services import create_new_order_version

        return create_new_order_version(
            order=self,
            contract=contract,
            start_date=start_date,
            end_date=end_date,
            copy_engagement_assignments=copy_engagement_assignments,
        )


class OrderVersion(models.Model):
    """Define OrderVersion model."""

    objects = OrderVersionManager()

    order = models.ForeignKey(Order, related_name="versions", on_delete=models.CASCADE)
    contract = models.OneToOneField(Contract, related_name="order_version", on_delete=models.CASCADE)
    version_number = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        """Define meta options for OrderVersion."""

        unique_together = (("order", "version_number"),)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Override init method to ensure start_date and end_date are instances of datetime.date."""
        super().__init__(*args, **kwargs)

    def __str__(self) -> str:
        """Return string representation of OrderVersion."""
        return f"Order: {self.order.id}, Version: {self.version_number}"

    def active(self, date: date = date.today()) -> bool:  # noqa: B008
        """Return whether the order version is active."""
        return self.start_date <= date <= self.end_date

    def clean(self) -> None:
        """Clean OrderVersion."""
        super().clean()
        if not isinstance(self.start_date, date):
            raise ValidationError("Start date must be a date.")
        if not isinstance(self.end_date, date):
            raise ValidationError("End date must be a date.")

        if self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be before start date."})

        previous_versions = (
            OrderVersion.objects.filter(order=self.order).exclude(id=self.id).order_by("-version_number")
        )

        # Ensure there are no breaks between versions
        if previous_versions.exists():
            latest_version = previous_versions.first()
            assert latest_version is not None
            if latest_version.end_date != self.start_date - timedelta(days=1):
                raise ValidationError("There cannot be breaks between versions.")

        overlapping_versions = OrderVersion.objects.filter(
            order=self.order, start_date__lt=self.end_date, end_date__gt=self.start_date
        ).exclude(id=self.id)
        if overlapping_versions.exists():
            raise ValidationError("There cannot be more than one active version at the same time.")

    def save(self, *args: Any, **kwargs: Any) -> None:
        """Override save method to call clean method before saving."""
        self.clean()
        super().save(*args, **kwargs)
