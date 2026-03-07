"""
Management command para diagnosticar y probar la extracción de texto.

Uso:
    python manage.py test_extraction <document_id>
    python manage.py test_extraction --all
"""
import logging
from django.core.management.base import BaseCommand
from documents.models import Document
from documents.services.extraction import extract_text_hybrid
from documents.services.summarization import summarize_text


class Command(BaseCommand):
    help = "Diagnostica la extracción de texto y resumen de un documento"

    def add_arguments(self, parser):
        parser.add_argument("document_id", nargs="?", type=int, help="ID del documento a probar")
        parser.add_argument("--all", action="store_true", help="Reprobar todos los documentos")
        parser.add_argument("--reprocess", action="store_true", help="Re-ejecutar pipeline completo")

    def handle(self, *args, **options):
        if options["verbosity"] >= 2:
            logging.basicConfig(level=logging.DEBUG)
            for name in ["documents.extraction", "documents.pipeline", "documents.summarization"]:
                logging.getLogger(name).setLevel(logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)

        if options.get("reprocess"):
            doc_id = options["document_id"]
            if not doc_id:
                self.stderr.write("Debes especificar un document_id con --reprocess")
                return
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"Reprocesando documento #{doc_id}...")
            self.stdout.write(f"{'='*60}\n")
            from documents.services.pipeline import process_document
            process_document(doc_id)
            self.stdout.write(self.style.SUCCESS("Pipeline ejecutado. Revisa los resultados."))
            options["all"] = False
            self._show_document(doc_id)
            return

        if options.get("all"):
            docs = Document.objects.all().order_by("id")
            for doc in docs:
                self._show_document(doc.id)
            return

        doc_id = options["document_id"]
        if not doc_id:
            self.stderr.write("Debes especificar un document_id o usar --all")
            return

        self._show_document(doc_id)

        # Probar extracción en vivo
        doc = Document.objects.get(id=doc_id)
        version = doc.versions.first()
        if version and version.file:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write("PROBANDO EXTRACCIÓN EN VIVO")
            self.stdout.write(f"{'='*60}")
            try:
                result = extract_text_hybrid(version.file.path)
                self.stdout.write(f"  Método: {'OCR' if result.used_ocr else 'Texto nativo'}")
                self.stdout.write(f"  Confianza: {result.ocr_confidence}")
                self.stdout.write(f"  Caracteres: {len(result.text)}")
                self.stdout.write(f"  Debug: {result.debug_info}")
                self.stdout.write(f"\n  TEXTO (primeros 800 chars):")
                self.stdout.write(f"  {'-'*40}")
                self.stdout.write(f"  {result.text[:800]}")

                if result.text:
                    self.stdout.write(f"\n  RESUMEN:")
                    self.stdout.write(f"  {'-'*40}")
                    summary = summarize_text(result.text)
                    self.stdout.write(f"  {summary}")
            except Exception as exc:
                self.stderr.write(f"  ERROR: {exc}")

    def _show_document(self, doc_id):
        try:
            doc = Document.objects.select_related("document_type", "suggested_type").get(id=doc_id)
        except Document.DoesNotExist:
            self.stderr.write(f"Documento #{doc_id} no encontrado")
            return

        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"DOCUMENTO #{doc.id}: {doc.title or '(sin título)'}")
        self.stdout.write(f"{'='*60}")
        self.stdout.write(f"  Tipo: {doc.document_type}")
        self.stdout.write(f"  Estado: {doc.status}")
        self.stdout.write(f"  OCR usado: {doc.is_ocr}")
        self.stdout.write(f"  Confianza OCR: {doc.ocr_confidence}")
        self.stdout.write(f"  Texto extraído: {len(doc.extracted_text)} chars")

        if doc.extracted_text:
            self.stdout.write(f"\n  TEXTO ALMACENADO (primeros 500 chars):")
            self.stdout.write(f"  {'-'*40}")
            self.stdout.write(f"  {doc.extracted_text[:500]}")
        else:
            self.stdout.write(self.style.WARNING("  ⚠ SIN TEXTO EXTRAÍDO"))

        summary = getattr(doc, "summary", None)
        if summary:
            self.stdout.write(f"\n  RESUMEN ALMACENADO:")
            self.stdout.write(f"  {'-'*40}")
            self.stdout.write(f"  {summary}")
        else:
            self.stdout.write(self.style.WARNING("  ⚠ SIN RESUMEN"))

        version = doc.versions.first()
        if version:
            self.stdout.write(f"\n  Archivo: {version.file.name}")
            self.stdout.write(f"  Ruta: {version.file.path}")
        else:
            self.stdout.write(self.style.WARNING("  ⚠ SIN ARCHIVO"))
