from django.db import migrations


DEFAULT_DOCUMENT_TYPES = (
    {"code": "CONTRACT", "name": "Contrato", "description": ""},
    {"code": "PO", "name": "Orden de compra", "description": ""},
    {"code": "CERT", "name": "Certificación", "description": ""},
)


def seed_document_types(apps, schema_editor):
    document_type_model = apps.get_model("documents", "DocumentType")

    for item in DEFAULT_DOCUMENT_TYPES:
        document_type_model.objects.update_or_create(
            code=item["code"],
            defaults={
                "name": item["name"],
                "description": item["description"],
                "is_active": True,
            },
        )


class Migration(migrations.Migration):

    dependencies = [
        ("documents", "0004_alter_auditlog_action"),
    ]

    operations = [
        migrations.RunPython(seed_document_types, migrations.RunPython.noop),
    ]
