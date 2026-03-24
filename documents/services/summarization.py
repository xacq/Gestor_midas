"""
Resumen extractivo offline usando sumy + NLTK.

Intenta usar LexRank como algoritmo principal. Si faltan dependencias
opcionales, cae a Luhn y, como último recurso, devuelve un extracto largo
del texto para evitar resúmenes inútilmente cortos.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("documents.summarization")
FALLBACK_SUMMARY_CHARS = 1500


def _ensure_nltk_data() -> None:
    """Descarga punkt_tab si no está disponible (solo la primera vez)."""
    import nltk
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        logger.info("Descargando datos NLTK (punkt_tab) por primera vez...")
        nltk.download("punkt_tab", quiet=True)


def _fallback_excerpt(text: str, max_chars: int = FALLBACK_SUMMARY_CHARS) -> str:
    excerpt = text[:max_chars]
    if len(text) > max_chars:
        last_space = excerpt.rfind(" ")
        if last_space > int(max_chars * 0.6):
            excerpt = excerpt[:last_space]
        excerpt += "..."
    return excerpt


def summarize_text(text: str, num_sentences: int = 8, language: str = "spanish") -> str:
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
        from sumy.summarizers.luhn import LuhnSummarizer
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
        stop_words = get_stop_words(language)

        for algorithm_name, summarizer_class in (
            ("LexRank", LexRankSummarizer),
            ("Luhn", LuhnSummarizer),
        ):
            try:
                summarizer = summarizer_class(stemmer)
                summarizer.stop_words = stop_words
                summary_sentences = list(summarizer(parser.document, num_sentences))
                if not summary_sentences:
                    logger.warning("%s no produjo oraciones; probando otro algoritmo", algorithm_name)
                    continue

                summary = " ".join(str(sentence) for sentence in summary_sentences)
                logger.info(
                    "Resumen generado con %s: %d oraciones, %d chars (de %d originales)",
                    algorithm_name, len(summary_sentences), len(summary), len(stripped),
                )
                return summary
            except Exception as exc:
                logger.warning(
                    "Fallo %s al generar resumen: %s. Se intentará otro algoritmo.",
                    algorithm_name,
                    exc,
                )

    except Exception as exc:
        logger.error("Error al generar resumen: %s", exc, exc_info=True)

    logger.warning(
        "No fue posible generar un resumen extractivo; se devolverá un extracto largo del texto."
    )
    return _fallback_excerpt(stripped)
