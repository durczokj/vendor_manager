"""Define permissions for engagements app."""

from rolepermissions.permissions import register_object_checker


@register_object_checker()
def access_engagement(role, user, engagement):
    """Check if user has access to the engagement."""
    del role
    return type(engagement).objects.accessible_to(user).filter(pk=engagement.pk).exists()


@register_object_checker()
def access_engagement_order_version_assignment(role, user, assignment):
    """Check if user has access to the engagement order version assignment."""
    del role
    return type(assignment).objects.accessible_to(user).filter(pk=assignment.pk).exists()


@register_object_checker()
def access_engagement_undertaking_assignment(role, user, assignment):
    """Check if user has access to the engagement undertaking assignment."""
    del role
    return type(assignment).objects.accessible_to(user).filter(pk=assignment.pk).exists()
