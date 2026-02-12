from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone
from .models import Document

@login_required
def manager_dashboard(request):
    today = timezone.localdate()
    in_30 = today + timedelta(days=30)

    published = Document.objects.select_related("document_type").filter(
        status=Document.Status.PUBLISHED,
        enabled=True,
    )

    contracts = published.filter(document_type__code="CONTRACT")
    contracts_active = contracts.filter(metadata__date_end__isnull=False, metadata__date_end__gte=today)
    contracts_expiring = contracts.filter(metadata__date_end__isnull=False, metadata__date_end__gte=today, metadata__date_end__lte=in_30)

    pos = published.filter(document_type__code="PO")

    kpis = {
        "published_total": published.count(),
        "contracts_total": contracts.count(),
        "contracts_active": contracts_active.count(),
        "contracts_expiring_30": contracts_expiring.count(),
        "contracts_amount_sum": contracts.aggregate(s=Sum("metadata__amount"))["s"] or 0,
        "po_total": pos.count(),
        "po_amount_sum": pos.aggregate(s=Sum("metadata__amount"))["s"] or 0,
    }

    expiring_list = contracts_expiring.order_by("metadata__date_end")[:20]
    recent_published = published.order_by("-updated_at")[:15]

    return render(request, "manager/dashboard.html", {
        "kpis": kpis,
        "expiring_list": expiring_list,
        "recent_published": recent_published,
        "today": today,
        "in_30": in_30,
    })
