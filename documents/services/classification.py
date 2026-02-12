import re

TYPE_RULES = {
    "CONTRACT": [
        r"\bcláusul[aa]s?\b",
        r"\bcontratante\b",
        r"\bcontratista\b",
        r"\bobjeto\b",
        r"\bplazo\b",
        r"\bvalor\b|\bmonto\b",
    ],
    "PO": [
        r"\borden de compra\b",
        r"\bitem\b",
        r"\bcantidad\b",
        r"\bproveedor\b",
        r"\btotal\b",
    ],
    "CERT": [
        r"\bcertifica\b|\bcertificación\b",
        r"\bnotar[ií]a\b",
        r"\bcompareciente\b",
        r"\bfe de\b",
        r"\bsello\b|\bfirma\b",
    ],
}


def classify_document(text: str) -> tuple[str, float]:
    t = (text or "").lower()
    best_code = "CONTRACT"
    best_score = 0.0

    for code, patterns in TYPE_RULES.items():
        score = 0
        for p in patterns:
            if re.search(p, t, flags=re.IGNORECASE):
                score += 1
        norm = score / max(len(patterns), 1)
        if norm > best_score:
            best_score = norm
            best_code = code

    return best_code, float(best_score)
