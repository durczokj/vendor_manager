from django.db import models
from django.core.exceptions import ValidationError
from companies.models import Company
from django.utils import timezone
from contracts.models import Contract
from datetime import timedelta, date
from django.db import transaction

class Order(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, related_name='orders', on_delete=models.CASCADE)

    def create_new_version(self, contract, start_date, end_date, copy_engagement_assignments=True):
        with transaction.atomic():
            last_version = self.versions.order_by('-version_number').first()

            last_version.end_date = start_date - timedelta(days=1)
            last_version.save()

            contract.save()

            new_version = OrderVersion(
                order = self,
                contract = contract,
                version_number = last_version.version_number + 1,
                start_date = start_date,
                end_date = end_date)
            
            new_version.save()

            if copy_engagement_assignments:
                for assignment in last_version.engagement_assignments.all():
                    assignment.pk = None
                    assignment.order_version = new_version
                    assignment.save()

class OrderVersion(models.Model):
    order = models.ForeignKey(Order, related_name='versions', on_delete=models.CASCADE)
    contract = models.OneToOneField(Contract, related_name='order_version', on_delete=models.CASCADE)
    version_number = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = (('order', 'version_number'),)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure start_date and end_date are instances of datetime.date
        if not isinstance(self.start_date, date):
            raise ValidationError("Start date must be a date.")
        if not isinstance(self.end_date, date):
            raise ValidationError("End date must be a date.")

    def __str__(self):
        return f"Order: {self.order.id}, Version: {self.version_number}"
    
    @property
    def active(self):
        return self.start_date <= timezone.now().date() <= self.end_date

    def clean(self):
        super().clean()

        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")

        previous_versions = OrderVersion.objects.filter(order=self.order).exclude(id=self.id).order_by('-version_number')

        # Ensure there are no breaks between versions
        if previous_versions.exists():
            latest_version = previous_versions.first()

            if latest_version.end_date != self.start_date - timezone.timedelta(days=1):
                raise ValidationError("There cannot be breaks between versions.")

        overlapping_versions = OrderVersion.objects.filter(
            order=self.order,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        ).exclude(id=self.id)
        if overlapping_versions.exists():
            raise ValidationError("There cannot be more than one active version at the same time.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
