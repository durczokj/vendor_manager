from rolepermissions.permissions import register_object_checker
from vendor_manager.roles import Person, Admin, UndertakingManager

@register_object_checker()
def access_person(role, user, person):
    if role == Admin:
        return True
    
    if role == UndertakingManager:
        return True

    if role == Person:
        if person.user == user:
            return True

    return False