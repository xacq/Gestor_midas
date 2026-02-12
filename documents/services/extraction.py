from __future__ import annotations

from dataclasses import dataclass
import os
import re

from django.conf import settings
from pypdf import PdfReader
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageOps


@dataclass
class ExtractionResult:
    text: str
    used_ocr: bool
    ocr_confidence: float | None


def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    parts: list[str] = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def preprocess_for_ocr(img: Image.Image) -> Image.Image:
    """
    Preprocesado ligero (sin OpenCV) para reducir ruido OCR:
    - escala de grises
    - autocontrast
    - binarización por umbral
    """
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)

    # umbral: ajusta 150-190 según tus scans. 160 suele funcionar bien.
    threshold = 160
    img = img.point(lambda x: 0 if x < threshold else 255, "1")
    return img.convert("L")


def normalize_text(text: str) -> str:
    """
    Limpieza post-OCR:
    - normaliza saltos/espacios
    - elimina líneas muy corruptas (muchos símbolos raros)
    """
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    cleaned_lines: list[str] = []
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln:
            cleaned_lines.append("")
            continue
        # “líneas corruptas”: demasiados símbolos raros
        weird_chars = "�§©®™{}[]|`~"
        weird = sum(1 for ch in ln if ch in weird_chars)
        if weird / max(len(ln), 1) > 0.15:
            continue
        cleaned_lines.append(ln)
    return "\n".join(cleaned_lines).strip()


def ocr_pdf(pdf_path: str) -> ExtractionResult:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    tessdata_dir = getattr(settings, "TESSDATA_DIR", None)
    if not tessdata_dir or not os.path.isdir(tessdata_dir):
        raise RuntimeError(f"TESSDATA_DIR no válido o no existe: {tessdata_dir}")

    images = convert_from_path(
        pdf_path,
        dpi=300,  # subimos dpi para más precisión en escaneos
        poppler_path=getattr(settings, "POPPLER_PATH", None),
    )

    # oem 1: LSTM (mejor calidad)
    # psm 6: bloque de texto uniforme (suele ir bien en contratos/OC)
    config = f'--tessdata-dir "{tessdata_dir}" --oem 1 --psm 6'

    text_parts: list[str] = []
    for img in images:
        img2 = preprocess_for_ocr(img)
        txt = pytesseract.image_to_string(img2, lang="spa+eng", config=config)
        text_parts.append(txt)

    text = normalize_text("\n".join(text_parts))
    return ExtractionResult(text=text, used_ocr=True, ocr_confidence=None)


def extract_text_hybrid(pdf_path: str, min_chars: int = 200) -> ExtractionResult:
    # 1) Intento texto embebido
    text = extract_text_from_pdf(pdf_path)
    text = normalize_text(text)

    if text and len(text) >= min_chars:
        return ExtractionResult(text=text, used_ocr=False, ocr_confidence=None)

    # 2) OCR si texto insuficiente
    return ocr_pdf(pdf_path)
