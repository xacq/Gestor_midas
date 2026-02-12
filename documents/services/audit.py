from typing import Any
from django.http import HttpRequest
from documents.models import AuditLog, AuditAction, Document


def _get_ip(request: HttpRequest) -> str:
    # Si hay proxy, opcional: HTTP_X_FORWARDED_FOR
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "") or ""


def log_event(
    *,
    request: HttpRequest | None,
    action: str,
    actor,
    document: Document | None = None,
    message: str = "",
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    ip = _get_ip(request) if request else ""
    ua = request.META.get("HTTP_USER_AGENT", "") if request else ""

    return AuditLog.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        document=document,
        ip_address=ip,
        user_agent=ua,
        message=message[:255] if message else "",
        metadata=metadata,
    )
