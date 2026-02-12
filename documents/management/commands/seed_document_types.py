from django.core.management.base import BaseCommand
from documents.models import DocumentType


class Command(BaseCommand):
    help = "Crea los tipos documentales iniciales (Contrato, Orden de compra, Certificación)."

    def handle(self, *args, **options):
        data = [
            {"code": "CONTRACT", "name": "Contrato"},
            {"code": "PO", "name": "Orden de compra"},
            {"code": "CERT", "name": "Certificación"},
        ]

        created = 0
        for item in data:
            obj, was_created = DocumentType.objects.get_or_create(
                code=item["code"],
                defaults={"name": item["name"], "is_active": True},
            )
            if not was_created:
                # si ya existe, asegúralo activo y con nombre correcto
                obj.name = item["name"]
                obj.is_active = True
                obj.save(update_fields=["name", "is_active"])
            else:
                created += 1

        self.stdout.write(self.style.SUCCESS(f"Tipos documentales listos. Nuevos creados: {created}"))
