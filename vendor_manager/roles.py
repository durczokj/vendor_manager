from rolepermissions.roles import AbstractUserRole

class Person(AbstractUserRole):
    available_permissions = {
        'view_person': True,
        'view_order': False,
        'view_company': True,
        'view_undertaking': True,
        'view_engagement': True,
        'view_leave': True,
    }

class UndertakingManager(AbstractUserRole):
    available_permissions = {
        'view_person': True,
        'view_order': True,
        'view_company': True,
        'view_undertaking': True,
        'view_engagement': True,
        'view_leave': True,
    }

class Admin(AbstractUserRole):
    available_permissions = {
        'view_person': True,
        'view_order': True,
        'view_company': True,
        'view_undertaking': True,
        'view_engagement': True,
        'view_leave': True,
    }