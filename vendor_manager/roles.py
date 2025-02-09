"""Define the roles for the application."""

from rolepermissions.roles import AbstractUserRole


class Person(AbstractUserRole):
    """Person role."""

    available_permissions = {
        "view_person": True,
        "view_order": False,
        "view_company": True,
        "view_undertaking": True,
        "view_engagement": True,
        "view_leave": True,
    }


class UndertakingManager(AbstractUserRole):
    """Undertaking Manager role."""

    available_permissions = {
        "view_person": True,
        "view_order": True,
        "view_company": True,
        "view_undertaking": True,
        "view_engagement": True,
        "view_leave": True,
    }


class Admin(AbstractUserRole):
    """Admin role."""

    available_permissions = {
        "view_person": True,
        "view_order": True,
        "view_company": True,
        "view_undertaking": True,
        "view_engagement": True,
        "view_leave": True,
    }
