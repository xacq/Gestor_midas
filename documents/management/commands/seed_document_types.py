from django.core.management.base import BaseCommand
from documents.models import DocumentType
from documents.services.document_types import DEFAULT_DOCUMENT_TYPES


class Command(BaseCommand):
    help = "Crea los tipos documentales iniciales (Contrato, Orden de compra, Certificación)."

    def handle(self, *args, **options):
        created = 0
        for item in DEFAULT_DOCUMENT_TYPES:
            obj, was_created = DocumentType.objects.get_or_create(
                code=item["code"],
                defaults={
                    "name": item["name"],
                    "description": item["description"],
                    "is_active": True,
                },
            )
            if not was_created:
                # si ya existe, asegúralo activo y con nombre correcto
                obj.name = item["name"]
                obj.description = item["description"]
                obj.is_active = True
                obj.save(update_fields=["name", "description", "is_active"])
            else:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Tipos documentales listos. Nuevos creados: {created}"))
