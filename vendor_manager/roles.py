"""Define the roles for the application."""

from rolepermissions.roles import AbstractUserRole


class Person(AbstractUserRole):
    """Person role."""

    available_permissions = {
        "view_person": True,
        "view_order": False,
        "view_company": False,
        "view_undertaking": False,
        "view_engagement": False,
        "view_engagement_order_version_assignment": False,
        "view_engagement_undertaking_version_assignment": False,
        "view_leave": True,
        "view_contract": False,
        "manage_person": False,
        "manage_order": False,
        "manage_company": False,
        "manage_undertaking": False,
        "manage_engagement": False,
        "manage_engagement_order_version_assignment": False,
        "view_engagement_undertaking_version_assignment": False,
        "manage_leave": True,
        "manage_contract": False,
    }


class UndertakingManager(AbstractUserRole):
    """Undertaking Manager role."""

    available_permissions = {
        "view_person": True,
        "view_order": True,
        "view_company": True,
        "view_undertaking": True,
        "view_engagement": True,
        "view_engagement_order_version_assignment": True,
        "view_engagement_undertaking_version_assignment": True,
        "view_leave": True,
        "view_contract": True,
        "manage_person": False,
        "manage_order": False,
        "manage_company": False,
        "manage_undertaking": True,
        "manage_engagement": False,
        "manage_engagement_order_version_assignment": False,
        "view_engagement_undertaking_version_assignment": False,
        "manage_leave": False,
        "manage_contract": False,
    }


class Admin(AbstractUserRole):
    """Admin role."""

    available_permissions = {
        "view_person": True,
        "view_order": True,
        "view_company": True,
        "view_undertaking": True,
        "view_engagement": True,
        "view_engagement_order_version_assignment": True,
        "view_engagement_undertaking_version_assignment": True,
        "view_leave": True,
        "view_contract": True,
        "manage_person": True,
        "manage_order": True,
        "manage_company": True,
        "manage_undertaking": True,
        "manage_engagement": True,
        "manage_engagement_order_version_assignment": True,
        "view_engagement_undertaking_version_assignment": True,
        "manage_leave": True,
        "manage_contract": False,
    }
