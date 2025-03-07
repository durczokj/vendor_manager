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
        "manage_person": False,
        "manage_order": False,
        "manage_company": False,
        "manage_undertaking": False,
        "manage_engagement": False,
        "manage_leave": True,
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
        "manage_person": False,
        "manage_order": False,
        "manage_company": False,
        "manage_undertaking": True,
        "manage_engagement": False,
        "manage_leave": True,
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
        "manage_person": True,
        "manage_order": True,
        "manage_company": True,
        "manage_undertaking": True,
        "manage_engagement": True,
        "manage_leave": True,
    }
