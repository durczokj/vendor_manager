"""Define permissions for leaves app."""

from rolepermissions.permissions import register_object_checker


@register_object_checker()
def access_leave(role, user, leave):
    """Check if user has access to the leave."""
    del role
    return type(leave).objects.accessible_to(user).filter(pk=leave.pk).exists()
