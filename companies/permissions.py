from rolepermissions.permissions import register_object_checker
from vendor_manager.roles import Person, Admin, UndertakingManager

@register_object_checker()
def access_company(role, user, company):
    if role == Admin:
        return True
    
    if role == UndertakingManager:
        return True

    if role == Person:
        companies = [e.order.company for e in user.person.engagements.all()]
        if company in companies:
            return True

    return False