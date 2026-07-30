from django.db import migrations


def rename_permission_codenames(apps, schema_editor):
    """Rename legacy engagement undertaking permission codenames."""
    Permission = apps.get_model("auth", "Permission")
    version_suffix = "version_assignment"

    codename_map = {
        f"view_engagement_undertaking_{version_suffix}": "view_engagement_undertaking_assignment",
        f"add_engagement_undertaking_{version_suffix}": "add_engagement_undertaking_assignment",
        f"change_engagement_undertaking_{version_suffix}": "change_engagement_undertaking_assignment",
        f"delete_engagement_undertaking_{version_suffix}": "delete_engagement_undertaking_assignment",
    }

    for old_codename, new_codename in codename_map.items():
        for old_permission in Permission.objects.filter(codename=old_codename):
            new_permission = Permission.objects.filter(
                content_type=old_permission.content_type,
                codename=new_codename,
            ).first()
            if new_permission is None:
                old_permission.codename = new_codename
                old_permission.save(update_fields=["codename"])
                continue

            new_permission.group_set.add(*old_permission.group_set.all())
            new_permission.user_set.add(*old_permission.user_set.all())
            old_permission.delete()


def revert_permission_codenames(apps, schema_editor):
    """Revert engagement undertaking permission codename renames."""
    Permission = apps.get_model("auth", "Permission")
    version_suffix = "version_assignment"

    codename_map = {
        "view_engagement_undertaking_assignment": f"view_engagement_undertaking_{version_suffix}",
        "add_engagement_undertaking_assignment": f"add_engagement_undertaking_{version_suffix}",
        "change_engagement_undertaking_assignment": f"change_engagement_undertaking_{version_suffix}",
        "delete_engagement_undertaking_assignment": f"delete_engagement_undertaking_{version_suffix}",
    }

    for old_codename, new_codename in codename_map.items():
        for old_permission in Permission.objects.filter(codename=old_codename):
            new_permission = Permission.objects.filter(
                content_type=old_permission.content_type,
                codename=new_codename,
            ).first()
            if new_permission is None:
                old_permission.codename = new_codename
                old_permission.save(update_fields=["codename"])
                continue

            new_permission.group_set.add(*old_permission.group_set.all())
            new_permission.user_set.add(*old_permission.user_set.all())
            old_permission.delete()


class Migration(migrations.Migration):
    """Rename legacy engagement undertaking permission codenames."""

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("engagements", "0001_initial_squashed_0011_rename_identifier_engagement_id"),
    ]

    operations = [
        migrations.RunPython(rename_permission_codenames, revert_permission_codenames),
    ]
