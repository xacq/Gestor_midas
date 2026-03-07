"""
Resumen extractivo offline usando sumy + NLTK.

Funciona 100% offline después de descargar los datos de NLTK una vez.
Usa LexRank (basado en similitud coseno entre oraciones) como algoritmo
principal — buen balance calidad/velocidad para documentos legales/comerciales.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("documents.summarization")


def _ensure_nltk_data() -> None:
    """Descarga punkt_tab si no está disponible (solo la primera vez)."""
    import nltk
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        logger.info("Descargando datos NLTK (punkt_tab) por primera vez...")
        nltk.download("punkt_tab", quiet=True)


def summarize_text(text: str, num_sentences: int = 5, language: str = "spanish") -> str:
    """
    Genera un resumen extractivo del texto usando LexRank.

    Args:
        text: Texto completo del documento.
        num_sentences: Número de oraciones a extraer para el resumen.
        language: Idioma del texto (para tokenización).

    Returns:
        Resumen como cadena de texto. Si el texto es muy corto, devuelve
        el texto original (o un fragmento).
    """
    if not text or not text.strip():
        logger.warning("Texto vacío, no se puede generar resumen")
        return ""

    # Texto demasiado corto: devolver como está
    stripped = text.strip()
    if len(stripped) < 100:
        logger.info("Texto muy corto (%d chars), devolviendo sin resumir", len(stripped))
        return stripped

    try:
        _ensure_nltk_data()

        from sumy.parsers.plaintext import PlaintextParser
        from sumy.nlp.tokenizers import Tokenizer
        from sumy.summarizers.lex_rank import LexRankSummarizer
        from sumy.nlp.stemmers import Stemmer
        from sumy.utils import get_stop_words

        parser = PlaintextParser.from_string(stripped, Tokenizer(language))

        # Verificar que hay suficientes oraciones
        sentences_in_doc = list(parser.document.sentences)
        if len(sentences_in_doc) <= num_sentences:
            logger.info(
                "Documento tiene solo %d oraciones (< %d), devolviendo texto completo",
                len(sentences_in_doc), num_sentences,
            )
            return stripped

        stemmer = Stemmer(language)
        summarizer = LexRankSummarizer(stemmer)
        summarizer.stop_words = get_stop_words(language)

        summary_sentences = summarizer(parser.document, num_sentences)

        summary = " ".join(str(s) for s in summary_sentences)
        logger.info(
            "Resumen generado: %d oraciones, %d chars (de %d originales)",
            len(list(summary_sentences)), len(summary), len(stripped),
        )
        return summary

    except Exception as exc:
        logger.error("Error al generar resumen: %s", exc, exc_info=True)
        # Fallback: devolver los primeros ~500 caracteres como extracto
        fallback = stripped[:500]
        if len(stripped) > 500:
            # Cortar en el último espacio para no partir palabras
            last_space = fallback.rfind(" ")
            if last_space > 200:
                fallback = fallback[:last_space] + "..."
        return fallback
