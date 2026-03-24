import logging

from django.db import transaction
from documents.models import Document, DocumentMetadata, DocumentType
from .extraction import extract_text_hybrid
from .classification import classify_document
from .metadata import (
    find_dates, find_reference_number, find_amount, find_parties,
    find_date_by_keyword, find_purchase_order_number, find_amount_by_keyword,
)
from .summarization import summarize_text

logger = logging.getLogger("documents.pipeline")


def process_document(document_id: int) -> None:
    logger.info("=== Pipeline iniciado para documento #%d ===", document_id)

    doc = Document.objects.select_related("document_type").get(id=document_id)
    latest_version = doc.versions.first()
    if not latest_version:
        logger.warning("Documento #%d sin versiones, abortando pipeline", document_id)
        return

    pdf_path = latest_version.file.path
    logger.info("Archivo: %s", pdf_path)

    # 1) Extracción de texto
    try:
        extraction = extract_text_hybrid(pdf_path)
        doc.extracted_text = extraction.text
        doc.is_ocr = extraction.used_ocr
        doc.ocr_confidence = extraction.ocr_confidence
        logger.info(
            "Extracción OK: %d chars, OCR=%s, confianza=%s",
            len(extraction.text), extraction.used_ocr, extraction.ocr_confidence,
        )
    except Exception as exc:
        logger.error("Error en extracción: %s", exc, exc_info=True)
        doc.extracted_text = ""
        doc.is_ocr = False
        doc.ocr_confidence = None
        extraction = None

    text = doc.extracted_text

    # 2) Clasificación sugerida
    if text:
        try:
            code, score = classify_document(text)
            suggested = DocumentType.objects.filter(code=code).first()
            doc.suggested_type = suggested
            doc.suggested_score = score
            logger.info("Clasificación: %s (score=%.2f)", code, score)
        except Exception as exc:
            logger.error("Error en clasificación: %s", exc, exc_info=True)
    else:
        logger.warning("Sin texto para clasificar")

    doc_type_code = ""
    if doc.suggested_type:
        doc_type_code = doc.suggested_type.code.upper()
    elif doc.document_type:
        doc_type_code = doc.document_type.code.upper()

    # 3) Metadatos sugeridos
    metadata_values = {
        "reference_number": None,
        "amount": None,
        "parties": None,
        "date_start": None,
        "date_end": None,
        "date_main": None,
    }

    if text:
        try:
            dates = find_dates(text)
            ref = find_reference_number(text)
            amount = find_amount(text)
            parties = find_parties(text)

            date_start = None
            date_end = None

            if doc_type_code == "PO":
                ref2 = find_purchase_order_number(text)
                if ref2:
                    ref = ref2

            amount2 = find_amount_by_keyword(text)
            if amount2:
                amount = amount2

            if doc_type_code == "CONTRACT":
                date_start = find_date_by_keyword(
                    text,
                    r"(fecha\s+de\s+inicio|inicio\s+de\s+vigencia|vigencia\s+desde)"
                )
                date_end = find_date_by_keyword(
                    text,
                    r"(fecha\s+de\s+terminaci[oó]n|fin\s+de\s+vigencia|vigencia\s+hasta)"
                )
                amount2 = find_amount_by_keyword(text)
                if amount2:
                    amount = amount2

            metadata_values.update({
                "reference_number": ref,
                "amount": amount,
                "parties": parties,
                "date_start": date_start,
                "date_end": date_end,
                "date_main": dates[0] if dates else None,
            })

            logger.info(
                "Metadatos: ref=%s, monto=%s, partes=%s, fechas=%s",
                ref, amount, parties[:60] if parties else "", dates[:3] if dates else [],
            )
        except Exception as exc:
            logger.error("Error en extracción de metadatos: %s", exc, exc_info=True)
    else:
        logger.warning("Sin texto para extraer metadatos")

    # 4) Resumen automático (NLP offline)
    if text:
        try:
            summary = summarize_text(text, num_sentences=100)
            doc.summary = summary
            logger.info("Resumen generado: %d chars", len(summary))
        except Exception as exc:
            logger.error("Error al generar resumen: %s", exc, exc_info=True)
            doc.summary = ""
    else:   
        doc.summary = ""
        logger.warning("Sin texto para generar resumen")

    # Auditoría
    from documents.services.audit import log_event
    from documents.models import AuditAction

    debug_info = {}
    if extraction and hasattr(extraction, "debug_info"):
        debug_info = extraction.debug_info

    # Guardar cambios en una transacción corta para minimizar locks en SQLite
    with transaction.atomic():
        if text:
            metadata, _ = DocumentMetadata.objects.get_or_create(document=doc)
            metadata.reference_number = metadata_values["reference_number"]
            metadata.amount = metadata_values["amount"]
            metadata.parties = metadata_values["parties"]
            metadata.date_start = metadata_values["date_start"]
            metadata.date_end = metadata_values["date_end"]
            if metadata.date_main is None and metadata_values["date_main"]:
                metadata.date_main = metadata_values["date_main"]
            metadata.save()

        doc.save()

        log_event(
            request=None,
            action=AuditAction.OCR_EXTRACT,
            actor=None,
            document=doc,
            message="Extracción automática ejecutada",
            metadata={
                "used_ocr": doc.is_ocr,
                "ocr_confidence": doc.ocr_confidence,
                "suggested_type": (doc.suggested_type.code if doc.suggested_type else None),
                "suggested_score": doc.suggested_score,
                "text_chars": len(doc.extracted_text),
                "summary_chars": len(doc.summary) if doc.summary else 0,
                "debug": debug_info,
            },
        )

    logger.info("=== Pipeline completado para documento #%d ===", document_id)
