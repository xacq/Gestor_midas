import re
from datetime import datetime
from decimal import Decimal


DATE_PATTERNS = [
    r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",     # 12/02/2026
    r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b",             # 2026-02-12
]


def find_dates(text: str):
    found = []
    for pat in DATE_PATTERNS:
        for m in re.finditer(pat, text):
            try:
                if "-" in m.group(0) and len(m.group(1)) == 4:
                    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
                else:
                    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    if y < 100:
                        y += 2000
                found.append(datetime(y, mo, d).date())
            except Exception:
                pass
    return found


def find_reference_number(text: str) -> str:
    # heurística: "N°", "No.", "Número", "OC", "Contrato"
    patterns = [
        r"(?:n[°o]\.?\s*|número\s*)([A-Z0-9\-\/]{4,})",
        r"(?:oc|orden)\s*[:#]?\s*([A-Z0-9\-\/]{4,})",
        r"(?:contrato)\s*[:#]?\s*([A-Z0-9\-\/]{4,})",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def find_amount(text: str) -> Decimal | None:
    # captura valores tipo 1.234,56 o 1234.56 (simplificado)
    m = re.search(r"\$\s*([0-9\.,]{3,})", text)
    if not m:
        return None
    raw = m.group(1)
    # normaliza: si tiene coma y punto, asume coma decimal (LATAM)
    raw = raw.replace(" ", "")
    if raw.count(",") == 1 and raw.count(".") >= 1:
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(",", "")
    try:
        return Decimal(raw)
    except Exception:
        return None


def find_parties(text: str) -> str:
    # muy simple: busca líneas con "CONTRATANTE", "CONTRATISTA", "PROVEEDOR"
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    hits = []
    for ln in lines[:250]:
        if any(k in ln.lower() for k in ["contratante", "contratista", "proveedor", "cliente"]):
            hits.append(ln)
    # devuelve concatenado corto
    return " | ".join(hits[:3])[:500]


def find_date_by_keyword(text: str, keyword_regex: str):
    # Busca “inicio: 12/02/2026”, “vigencia hasta 12/02/2027”, etc.
    import re
    from datetime import datetime

    m = re.search(keyword_regex + r".{0,40}?(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", text, flags=re.IGNORECASE)
    if not m:
        return None
    raw = m.group(1)
    d, mo, y = raw.replace("-", "/").split("/")
    y = int(y)
    if y < 100:
        y += 2000
    return datetime(int(y), int(mo), int(d)).date()


def find_purchase_order_number(text: str) -> str:
    import re
    patterns = [
        r"\bOC\b\s*[:#]?\s*([A-Z0-9\-\/]{4,})",
        r"\bOrden\s+de\s+Compra\b\s*[:#]?\s*([A-Z0-9\-\/]{4,})",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""

def find_amount_by_keyword(text: str):
    import re
    from decimal import Decimal

    m = re.search(r"(valor\s+total|monto\s+total|total)\s*[:\-]?\s*\$?\s*([0-9\.,]{3,})", text, flags=re.IGNORECASE)
    if not m:
        return None
    raw = m.group(2).replace(" ", "")
    if raw.count(",") == 1 and raw.count(".") >= 1:
        raw = raw.replace(".", "").replace(",", ".")
    else:
        raw = raw.replace(",", "")
    try:
        return Decimal(raw)
    except:
        return None
