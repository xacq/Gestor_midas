from django.db.models.signals import post_migrate
from django.dispatch import receiver

from .services.document_types import ensure_default_document_types


@receiver(post_migrate)
def seed_default_document_types(sender, app_config, apps, **kwargs):
    if app_config.label != "documents":
        return

    document_type_model = apps.get_model("documents", "DocumentType")
    ensure_default_document_types(document_type_model=document_type_model)
