"""Service layer for engagements."""

from django.db import transaction

from engagements.models import Engagement


@transaction.atomic
def update_engagement(*, engagement: Engagement) -> Engagement:
    """Persist an engagement and adjust child undertaking assignment date bounds."""
    engagement.save()

    for assignment in engagement.undertaking_assignments.all():
        assignment.start_date = max(engagement.start_date, assignment.start_date)
        assignment.end_date = min(engagement.end_date, assignment.end_date)
        assignment.save()

    return engagement
