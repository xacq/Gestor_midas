from django.db import transaction
from documents.models import Document, DocumentMetadata, DocumentType
from .extraction import extract_text_hybrid
from .classification import classify_document
from .metadata import find_dates, find_reference_number, find_amount, find_parties


@transaction.atomic
def process_document(document_id: int) -> None:
    doc = Document.objects.select_related("document_type").get(id=document_id)
    latest_version = doc.versions.first()
    if not latest_version:
        return

    pdf_path = latest_version.file.path

    # 1) extracción
    extraction = extract_text_hybrid(pdf_path)
    doc.extracted_text = extraction.text
    doc.is_ocr = extraction.used_ocr
    doc.ocr_confidence = extraction.ocr_confidence

    # 2) clasificación sugerida
    code, score = classify_document(extraction.text)
    suggested = DocumentType.objects.filter(code=code).first()
    doc.suggested_type = suggested
    doc.suggested_score = score

    doc_type_code = (suggested.code if suggested else (doc.document_type.code if doc.document_type else "")).upper()

    # 3) metadatos sugeridos
    dates = find_dates(extraction.text)
    ref = find_reference_number(extraction.text)
    amount = find_amount(extraction.text)
    parties = find_parties(extraction.text)

    date_start = None
    date_end = None

    if doc_type_code == "PO":
        ref2 = find_purchase_order_number(extraction.text)
        if ref2:
            ref = ref2
    amount2 = find_amount_by_keyword(extraction.text)
    if amount2:
        amount = amount2

    if doc_type_code == "CONTRACT":
        date_start = find_date_by_keyword(extraction.text, r"(fecha\s+de\s+inicio|inicio\s+de\s+vigencia|vigencia\s+desde)")
        date_end = find_date_by_keyword(extraction.text, r"(fecha\s+de\s+terminaci[oó]n|fin\s+de\s+vigencia|vigencia\s+hasta)")
        amount2 = find_amount_by_keyword(extraction.text)
        if amount2:
            amount = amount2

    # Guardar en metadata
    metadata, _ = DocumentMetadata.objects.get_or_create(document=doc)
    metadata.reference_number = ref
    metadata.amount = amount
    metadata.parties = parties
    metadata.date_start = date_start
    metadata.date_end = date_end
    if dates and not metadata.date_main:
        metadata.date_main = dates[0]
    metadata.save()

    from documents.services.audit import log_event
    from documents.models import AuditAction

    log_event(
        request=None,
        action=AuditAction.OCR_EXTRACT,
        actor=None,
        document=doc,
        message="Extracción automática ejecutada",
        metadata={
            "used_ocr": doc.is_ocr,
            "suggested_type": (doc.suggested_type.code if doc.suggested_type else None),
            "suggested_score": doc.suggested_score,
        },
    )

    doc.save()
