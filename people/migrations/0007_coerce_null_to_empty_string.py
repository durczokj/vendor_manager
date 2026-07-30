"""Data migration: coerce NULL description/location to empty string."""

from django.db import migrations


def coerce_nulls_to_empty_string(apps, schema_editor):
    """Set NULL description and location values to empty string."""
    Person = apps.get_model("people", "Person")
    Person.objects.filter(description__isnull=True).update(description="")
    Person.objects.filter(location__isnull=True).update(location="")


def reverse_coerce(apps, schema_editor):
    """No-op reverse: empty strings remain empty strings."""


class Migration(migrations.Migration):
    """Coerce NULL description/location fields to empty string before removing nullability."""

    dependencies = [
        ("people", "0001_initial_squashed_0006_rename_identifier_person_id"),
    ]

    operations = [
        migrations.RunPython(coerce_nulls_to_empty_string, reverse_coerce),
    ]
