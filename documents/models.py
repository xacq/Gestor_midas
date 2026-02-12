from django.conf import settings
from django.db import models
from django.utils import timezone


class DocumentType(models.Model):
    code = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Document(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Borrador"
        VALIDATED = "VALIDATED", "Validado"
        PUBLISHED = "PUBLISHED", "Publicado"

    title = models.CharField(max_length=255, blank=True, default="")
    document_type = models.ForeignKey(DocumentType, on_delete=models.PROTECT, related_name="documents")

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    enabled = models.BooleanField(default=True)

    # Sugerencia de clasificación (para luego)
    suggested_type = models.ForeignKey(
        DocumentType, on_delete=models.SET_NULL, null=True, blank=True, related_name="suggested_documents"
    )
    suggested_score = models.FloatField(null=True, blank=True)

    # Auditoría
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="documents_created"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Texto extraído/OCR (backend)
    extracted_text = models.TextField(blank=True, default="")
    is_ocr = models.BooleanField(default=False)
    ocr_confidence = models.FloatField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title or f"Documento #{self.pk}"


def document_upload_path(instance: "DocumentVersion", filename: str) -> str:
    # media/documents/<doc_id>/v<version>/<filename>
    return f"documents/{instance.document_id}/v{instance.version_number}/{filename}"


class DocumentVersion(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField(default=1)

    file = models.FileField(upload_to=document_upload_path)
    file_name = models.CharField(max_length=255, blank=True, default="")
    mime_type = models.CharField(max_length=120, blank=True, default="")
    file_hash_sha256 = models.CharField(max_length=64, blank=True, default="")
    file_size_bytes = models.BigIntegerField(null=True, blank=True)

    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("document", "version_number")]
        ordering = ["-version_number"]

    def __str__(self) -> str:
        return f"{self.document} v{self.version_number}"


class DocumentMetadata(models.Model):
    """
    Metadatos normalizados mínimos.
    Si luego quieres ampliar por tipo, podemos:
      - agregar más campos
      - o separar en tablas por tipo
    """
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name="metadata")

    parties = models.TextField(blank=True, default="")   # nombres/partes involucradas
    date_main = models.DateField(null=True, blank=True)
    date_start = models.DateField(null=True, blank=True)
    date_end = models.DateField(null=True, blank=True)

    reference_number = models.CharField(max_length=120, blank=True, default="")  # contrato/OC/cert ref
    amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)

    notes = models.TextField(blank=True, default="")

    def __str__(self) -> str:
        return f"Metadatos de {self.document_id}"


from django.db import models
from django.conf import settings

class AuditAction(models.TextChoices):
    UPLOAD = "UPLOAD", "Carga de documento"
    OCR_EXTRACT = "OCR_EXTRACT", "Extracción/OCR"
    REVIEW_SAVE = "REVIEW_SAVE", "Guardar revisión"
    VALIDATE = "VALIDATE", "Validar documento"
    PUBLISH = "PUBLISH", "Publicar documento"
    ENABLE = "ENABLE", "Habilitar documento"
    DISABLE = "DISABLE", "Inhabilitar documento"
    LOGIN = "LOGIN", "Inicio de sesión"
    LOGOUT = "LOGOUT", "Cierre de sesión"


class AuditLog(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    action = models.CharField(max_length=32, choices=AuditAction.choices, db_index=True)

    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )

    # Contexto DLP / trazabilidad
    ip_address = models.CharField(max_length=64, blank=True, default="")
    user_agent = models.TextField(blank=True, default="")

    # Información útil de auditoría
    message = models.CharField(max_length=255, blank=True, default="")
    metadata = models.JSONField(blank=True, null=True)  # diffs, scores, etc.

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        who = self.actor.username if self.actor else "system"
        return f"[{self.created_at}] {who} {self.action}"
