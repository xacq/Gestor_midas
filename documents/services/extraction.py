from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field

from django.conf import settings
from pypdf import PdfReader
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageOps, ImageFilter

logger = logging.getLogger("documents.extraction")


@dataclass
class ExtractionResult:
    text: str
    used_ocr: bool
    ocr_confidence: float | None
    debug_info: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Utilidades de preprocesamiento
# ---------------------------------------------------------------------------

def _upscale_if_needed(img: Image.Image, min_width: int = 1800) -> Image.Image:
    """Escala imágenes pequeñas para mejorar la precisión OCR."""
    w, h = img.size
    if w < min_width:
        factor = min_width / w
        new_size = (int(w * factor), int(h * factor))
        img = img.resize(new_size, Image.LANCZOS)
        logger.debug("Imagen escalada de %dx%d a %dx%d", w, h, *new_size)
    return img


def _preprocess_adaptive(img: Image.Image, threshold: int = 160) -> Image.Image:
    """
    Preprocesado mejorado:
    - escala de grises
    - autocontrast
    - desenfoque ligero para reducir ruido
    - binarización por umbral configurable
    """
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img, cutoff=1)
    # Desenfoque ligero para eliminar ruido puntual
    img = img.filter(ImageFilter.MedianFilter(size=3))
    img = img.point(lambda x: 0 if x < threshold else 255, "1")
    return img.convert("L")


# ---------------------------------------------------------------------------
# Extracción de texto nativo (PDF digital)
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extrae texto embebido de un PDF digital."""
    try:
        reader = PdfReader(pdf_path)
        parts: list[str] = []
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            parts.append(page_text)
            logger.debug("Página %d (nativo): %d caracteres", i + 1, len(page_text))
        return "\n".join(parts).strip()
    except Exception as exc:
        logger.error("Error extrayendo texto nativo del PDF: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# OCR mejorado
# ---------------------------------------------------------------------------

PSM_MODES = [
    (3, "Automático completo"),
    (6, "Bloque de texto uniforme"),
    (4, "Columna de texto"),
]

THRESHOLDS = [140, 160, 180]


def _ocr_page_with_confidence(
    img: Image.Image, lang: str, config_base: str
) -> tuple[str, float]:
    """
    Ejecuta OCR en una imagen y devuelve (texto, confianza_promedio).
    Usa image_to_data para obtener confianza por palabra.
    """
    data = pytesseract.image_to_data(img, lang=lang, config=config_base, output_type=pytesseract.Output.DICT)

    words = []
    confidences = []
    for i, conf in enumerate(data["conf"]):
        try:
            c = int(conf)
        except (ValueError, TypeError):
            continue
        if c < 0:
            continue
        word = (data["text"][i] or "").strip()
        if word:
            words.append(word)
            confidences.append(c)

    text = " ".join(words)
    avg_conf = sum(confidences) / max(len(confidences), 1) if confidences else 0.0
    return text, avg_conf


def _ocr_single_page(
    img: Image.Image, tessdata_dir: str, lang: str = "spa+eng"
) -> tuple[str, float, dict]:
    """
    Intenta múltiples combinaciones de PSM y umbrales de binarización.
    Devuelve el mejor resultado (más texto con confianza razonable).
    """
    best_text = ""
    best_conf = 0.0
    best_info = {}

    img = _upscale_if_needed(img)

    for psm, psm_name in PSM_MODES:
        config = f'--tessdata-dir "{tessdata_dir}" --oem 1 --psm {psm}'

        for threshold in THRESHOLDS:
            processed = _preprocess_adaptive(img, threshold=threshold)
            text, conf = _ocr_page_with_confidence(processed, lang, config)

            logger.debug(
                "PSM %d (%s), umbral %d: %d chars, confianza %.1f%%",
                psm, psm_name, threshold, len(text), conf,
            )

            # Elegir el resultado con más texto útil y confianza razonable
            score = len(text) * (conf / 100.0) if conf > 20 else 0
            best_score = len(best_text) * (best_conf / 100.0) if best_conf > 20 else 0

            if score > best_score:
                best_text = text
                best_conf = conf
                best_info = {
                    "psm": psm,
                    "psm_name": psm_name,
                    "threshold": threshold,
                    "chars": len(text),
                    "confidence": round(conf, 2),
                }

    return best_text, best_conf, best_info


def ocr_pdf(pdf_path: str) -> ExtractionResult:
    """Ejecuta OCR en todas las páginas del PDF con múltiples estrategias."""
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    tessdata_dir = getattr(settings, "TESSDATA_DIR", None)
    if not tessdata_dir or not os.path.isdir(tessdata_dir):
        raise RuntimeError(f"TESSDATA_DIR no válido o no existe: {tessdata_dir}")

    logger.info("Iniciando OCR para: %s", pdf_path)

    images = convert_from_path(
        pdf_path,
        dpi=300,
        poppler_path=getattr(settings, "POPPLER_PATH", None),
    )

    text_parts: list[str] = []
    all_confidences: list[float] = []
    page_details: list[dict] = []

    for page_num, img in enumerate(images, 1):
        logger.info("OCR página %d/%d ...", page_num, len(images))
        page_text, page_conf, page_info = _ocr_single_page(img, tessdata_dir)

        # Reconstruir texto con saltos de línea (image_to_data no los preserva bien)
        text_parts.append(page_text)
        all_confidences.append(page_conf)
        page_info["page"] = page_num
        page_details.append(page_info)

        logger.info(
            "Página %d: %d chars, confianza %.1f%%, PSM %s, umbral %s",
            page_num,
            page_info.get("chars", 0),
            page_info.get("confidence", 0),
            page_info.get("psm", "?"),
            page_info.get("threshold", "?"),
        )

    raw_text = "\n\n".join(text_parts)
    text = normalize_text(raw_text)
    avg_confidence = sum(all_confidences) / max(len(all_confidences), 1)

    logger.info(
        "OCR completado: %d chars totales, confianza promedio %.1f%%",
        len(text), avg_confidence,
    )

    return ExtractionResult(
        text=text,
        used_ocr=True,
        ocr_confidence=round(avg_confidence, 2),
        debug_info={
            "total_pages": len(images),
            "total_chars": len(text),
            "avg_confidence": round(avg_confidence, 2),
            "pages": page_details,
        },
    )


# ---------------------------------------------------------------------------
# Normalización de texto post-OCR (menos agresiva)
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Limpieza post-OCR mejorada: menos agresiva que la versión anterior.
    """
    if not text:
        return ""
    text = text.replace("\r", "\n")
    # Normalizar múltiples espacios/tabs (pero preservar saltos de línea)
    text = re.sub(r"[ \t]{2,}", " ", text)
    # Reducir saltos de línea excesivos
    text = re.sub(r"\n{4,}", "\n\n\n", text)

    cleaned_lines: list[str] = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            cleaned_lines.append("")
            continue
        # Solo descartar líneas con >30% de caracteres problemáticos
        # (antes era 15%, demasiado agresivo)
        weird_chars = "�§©®™{}|`~"
        weird = sum(1 for ch in ln if ch in weird_chars)
        ratio = weird / max(len(ln), 1)
        if ratio > 0.30:
            logger.debug("Línea descartada (%.0f%% chars raros): %s", ratio * 100, ln[:80])
            continue
        cleaned_lines.append(ln)
    return "\n".join(cleaned_lines).strip()


# ---------------------------------------------------------------------------
# Función principal: extracción híbrida
# ---------------------------------------------------------------------------

def extract_text_hybrid(pdf_path: str, min_chars: int = 200) -> ExtractionResult:
    """
    Estrategia híbrida mejorada:
    1. Intenta texto embebido (PDF digital)
    2. Si es insuficiente, aplica OCR con múltiples estrategias
    3. Si ambos producen texto, combina si el OCR aporta significativamente más
    """
    logger.info("Extracción híbrida iniciada para: %s", pdf_path)

    # 1) Texto embebido
    native_text = extract_text_from_pdf(pdf_path)
    native_text = normalize_text(native_text)
    logger.info("Texto nativo: %d caracteres", len(native_text))

    if native_text and len(native_text) >= min_chars:
        logger.info("Texto nativo suficiente (%d chars), saltando OCR", len(native_text))
        return ExtractionResult(
            text=native_text,
            used_ocr=False,
            ocr_confidence=None,
            debug_info={"method": "native", "chars": len(native_text)},
        )

    # 2) OCR
    logger.info("Texto nativo insuficiente (%d chars < %d), ejecutando OCR...", len(native_text), min_chars)
    try:
        ocr_result = ocr_pdf(pdf_path)
    except Exception as exc:
        logger.error("Error en OCR: %s", exc, exc_info=True)
        # Si OCR falla pero hay algo de texto nativo, devolver eso
        if native_text:
            logger.warning("OCR falló, devolviendo texto nativo parcial (%d chars)", len(native_text))
            return ExtractionResult(
                text=native_text,
                used_ocr=False,
                ocr_confidence=None,
                debug_info={"method": "native_fallback", "ocr_error": str(exc)},
            )
        raise

    # 3) Si hay texto nativo parcial y el OCR también produjo algo, usar el más largo
    if native_text and len(native_text) > len(ocr_result.text):
        logger.info("Texto nativo (%d) más largo que OCR (%d), usando nativo",
                     len(native_text), len(ocr_result.text))
        return ExtractionResult(
            text=native_text,
            used_ocr=False,
            ocr_confidence=None,
            debug_info={"method": "native_preferred", "native_chars": len(native_text),
                        "ocr_chars": len(ocr_result.text)},
        )

    return ocr_result
