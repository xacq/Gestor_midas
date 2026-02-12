from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import render
from documents.models import AuditLog


@staff_member_required
def audit_log_list(request):
    q = (request.GET.get("q") or "").strip()
    action = (request.GET.get("action") or "").strip()

    logs = AuditLog.objects.select_related("actor", "document")

    if action:
        logs = logs.filter(action=action)

    if q:
        logs = logs.filter(
            Q(message__icontains=q) |
            Q(actor__username__icontains=q) |
            Q(document__title__icontains=q)
        )

    logs = logs.order_by("-created_at")[:300]  # límite razonable
    return render(request, "audit/list.html", {"logs": logs, "q": q, "action": action})
