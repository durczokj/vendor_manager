"""Define permissions for engagements app."""

from typing import Any

from django.contrib.auth.models import User
from rolepermissions.permissions import register_object_checker

from engagements.models import (
    Engagement,
    EngagementOrderVersionAssignment,
    EngagementUndertakingAssignment,
)


@register_object_checker()
def access_engagement(role: Any, user: User, engagement: Engagement) -> bool:
    """Check if user has access to the engagement."""
    del role
    return type(engagement).objects.accessible_to(user).filter(pk=engagement.pk).exists()


@register_object_checker()
def access_engagement_order_version_assignment(
    role: Any, user: User, assignment: EngagementOrderVersionAssignment
) -> bool:
    """Check if user has access to the engagement order version assignment."""
    del role
    return type(assignment).objects.accessible_to(user).filter(pk=assignment.pk).exists()


@register_object_checker()
def access_engagement_undertaking_assignment(
    role: Any, user: User, assignment: EngagementUndertakingAssignment
) -> bool:
    """Check if user has access to the engagement undertaking assignment."""
    del role
    return type(assignment).objects.accessible_to(user).filter(pk=assignment.pk).exists()
