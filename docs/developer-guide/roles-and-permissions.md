# Roles & Permissions

Vendor Manager defines three roles using
[django-role-permissions](https://django-role-permissions.readthedocs.io/).
Role membership is stored in Django's standard `auth_user_groups` table — no custom user
model is required.

## Roles

| Role | Who holds it | Summary |
|---|---|---|
| `Person` | Vendor/contractor with a `Person` record | Can view and manage their own leaves only. |
| `UndertakingManager` | Internal project manager | Can view all records; can create/edit/delete undertakings. |
| `Admin` | Application administrator | Full access except contract mutation. |

## Permission matrix

A `✓` means the permission is **granted** by default for that role; `–` means it is
**denied**.

| Permission | Person | UndertakingManager | Admin |
|---|:---:|:---:|:---:|
| `view_person` | ✓ | ✓ | ✓ |
| `add_person` | – | – | ✓ |
| `change_person` | – | – | ✓ |
| `delete_person` | – | – | ✓ |
| `view_company` | – | ✓ | ✓ |
| `add_company` | – | – | ✓ |
| `change_company` | – | – | ✓ |
| `delete_company` | – | – | ✓ |
| `view_contract` | – | ✓ | ✓ |
| `add_contract` | – | – | – |
| `change_contract` | – | – | – |
| `delete_contract` | – | – | – |
| `view_order` | – | ✓ | ✓ |
| `add_order` | – | – | ✓ |
| `change_order` | – | – | ✓ |
| `delete_order` | – | – | ✓ |
| `view_undertaking` | – | ✓ | ✓ |
| `add_undertaking` | – | ✓ | ✓ |
| `change_undertaking` | – | ✓ | ✓ |
| `delete_undertaking` | – | ✓ | ✓ |
| `view_engagement` | – | ✓ | ✓ |
| `add_engagement` | – | – | ✓ |
| `change_engagement` | – | – | ✓ |
| `delete_engagement` | – | – | ✓ |
| `view_engagement_order_version_assignment` | – | ✓ | ✓ |
| `add_engagement_order_version_assignment` | – | – | ✓ |
| `change_engagement_order_version_assignment` | – | – | ✓ |
| `delete_engagement_order_version_assignment` | – | – | ✓ |
| `view_engagement_undertaking_assignment` | – | ✓ | ✓ |
| `add_engagement_undertaking_assignment` | – | – | ✓ |
| `change_engagement_undertaking_assignment` | – | – | ✓ |
| `delete_engagement_undertaking_assignment` | – | – | ✓ |
| `view_leave` | ✓ | ✓ | ✓ |
| `add_leave` | ✓ | – | ✓ |
| `change_leave` | ✓ | – | ✓ |
| `delete_leave` | ✓ | – | ✓ |

!!! note "Contract permissions"
    `add_contract`, `change_contract`, and `delete_contract` are denied for **all** roles.
    Contracts are managed externally and imported; no role in this application may mutate
    them directly.

## Source of truth

The role definitions live in
[`vendor_manager/roles.py`](https://github.com/durczokj/vendor_manager/blob/main/vendor_manager/roles.py).
The permission names above map directly to the `available_permissions` dict in that file.

For the broader context on how roles fit into the data model see the
[Architecture](architecture.md) page.
