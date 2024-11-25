from django.db import models
from django.core.exceptions import ValidationError
from companies.models import Company
from django.utils import timezone

class Order(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    company = models.ForeignKey(Company, related_name='orders', on_delete=models.CASCADE)

class OrderVersion(models.Model):
    order = models.ForeignKey(Order, related_name='versions', on_delete=models.CASCADE)
    version_number = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()

    class Meta:
        unique_together = (('order', 'version_number'),)

    def __str__(self):
        return f"Order: {self.order.id}, Version: {self.version_number}"
    
    @property
    def active(self):
        return self.start_date <= timezone.now().date() <= self.end_date

    def clean(self):
        super().clean()

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

        # Update engagements' start and end dates
        for engagement in self.engagements.all():
            engagement.start_date = max(self.start_date, engagement.start_date)
            engagement.end_date = min(self.end_date, engagement.end_date)
            engagement.save()

class Contract(models.Model):
    id = models.IntegerField(primary_key=True)
    order_version = models.OneToOneField(OrderVersion, related_name='contract', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    size = models.IntegerField()