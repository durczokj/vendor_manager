from django.db import models
from orders.models import OrderVersion
from people.models import Person
from undertakings.models import Undertaking
from django.core.exceptions import ValidationError
from datetime import date

class Engagement(models.Model):
    id = models.IntegerField(primary_key=True)
    order_version = models.ForeignKey(OrderVersion, related_name='engagements', on_delete=models.CASCADE)
    person = models.ForeignKey(Person, related_name='engagements', on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    fte = models.DecimalField(max_digits=3, decimal_places=2)

    @property
    def active(self):
        return (self.start_date <= date.today() <= self.end_date) and self.order_version.active
    
    class Meta:
        unique_together = (('order_version', 'person'),)

    def clean(self):
        super().clean()
        if not (0 < self.fte <= 1):
            raise ValidationError("FTE must be between 0 and 1.")
        if self.start_date < self.order_version.start_date:
            raise ValidationError("Engagement start date must be on or after the order version start date.")
        if self.end_date > self.order_version.end_date:
            raise ValidationError("Engagement end date must be on or before the order version end date.")

    def save(self, *args, **kwargs):
        self.clean()

        # Update assignments' start and end dates
        for assignment in self.assignments.all():
            assignment.start_date = max(self.start_date, assignment.start_date)
            assignment.end_date = min(self.end_date, assignment.end_date)
            assignment.save()

        super().save(*args, **kwargs)

class Assignment(models.Model):
    engagement = models.ForeignKey(Engagement, related_name='assignments', on_delete=models.CASCADE)
    undertaking = models.ForeignKey(Undertaking, related_name="assignments", on_delete=models.CASCADE)
    percentage = models.DecimalField(max_digits=3, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    @property
    def active(self):
        return self.engagement.active

    def clean(self):
        super().clean()
        if self.start_date < self.engagement.start_date or self.end_date > self.engagement.end_date:
            raise ValidationError("Assignment dates must be within the engagement period.")

        overlapping_assignments = Assignment.objects.filter(
            engagement=self.engagement,
            undertaking=self.undertaking,
            start_date__lt=self.end_date,
            end_date__gt=self.start_date
        ).exclude(id=self.id)
        if overlapping_assignments.exists():
            raise ValidationError("Assignments for the same engagement and undertaking cannot overlap.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)