from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Document
from django.shortcuts import redirect

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.shortcuts import render
from django.http import HttpResponseNotAllowed
from .forms import DocumentUploadForm
from .models import Document, DocumentVersion
from documents.services.pipeline import process_document

@login_required
def published_list(request):
    q = (request.GET.get("q") or "").strip()
    doc_type = (request.GET.get("type") or "").strip()

    qs = (
        Document.objects
        .select_related("document_type", "created_by")
        .filter(status=Document.Status.PUBLISHED, enabled=True)
    )

    if doc_type:
        qs = qs.filter(document_type__id=doc_type)

    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(extracted_text__icontains=q) |
            Q(metadata__parties__icontains=q) |
            Q(metadata__reference_number__icontains=q)
        )

    types = (
        Document.objects
        .filter(status=Document.Status.PUBLISHED, enabled=True)
        .values("document_type__id", "document_type__name")
        .distinct()
        .order_by("document_type__name")
    )

    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "documents": page_obj,
        "q": q,
        "types": types,
        "selected_type": doc_type,
    }
    return render(request, "documents/published_list.html", context)


@login_required
def document_detail(request, pk: int):
    doc = get_object_or_404(
        Document.objects.select_related("document_type", "created_by").prefetch_related("versions"),
        pk=pk,
        status=Document.Status.PUBLISHED,
        enabled=True,
    )

    latest_version = doc.versions.first()  # por ordering en model: -version_number
    return render(
        request,
        "documents/detail.html",
        {"doc": doc, "latest_version": latest_version},
    )


@login_required
def document_download(request, pk: int):
    """
    Vista auditable para descarga de documentos.
    Registra el evento y luego redirige al archivo físico.
    """
    doc = get_object_or_404(Document, pk=pk, enabled=True)
    version = doc.versions.first()
    if not version or not version.file:
        messages.error(request, "El documento no tiene un archivo asociado.")
        return redirect("document_detail", pk=pk)

    # Auditoría de descarga
    from documents.services.audit import log_event
    from documents.models import AuditAction
    log_event(
        request=request,
        action=AuditAction.DOWNLOAD,
        actor=request.user,
        document=doc,
        message=f"Descarga de archivo: {version.file_name}",
        metadata={"version": version.version_number, "filename": version.file_name}
    )

    return redirect(version.file.url)


@staff_member_required
def upload_document(request):
    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            messages.error(request, "Revisa el formulario. Hay campos inválidos o faltantes.")
            return render(request, "documents/upload.html", {"form": form})

        title = (form.cleaned_data.get("title") or "").strip()
        doc_type = form.cleaned_data["document_type"]
        pdf_file = form.cleaned_data["file"]

        document = Document.objects.create(
            title=title,
            document_type=doc_type,
            created_by=request.user,
            status=Document.Status.DRAFT,
        )

        DocumentVersion.objects.create(
            document=document,
            version_number=1,
            file=pdf_file,
            uploaded_by=request.user,
        )

        from documents.services.audit import log_event
        from documents.models import AuditAction

        log_event(
            request=request,
            action=AuditAction.UPLOAD,
            actor=request.user,
            document=document,
            message="Documento cargado por administrador",
            metadata={
                "filename": pdf_file.name,
                "document_type": str(doc_type.code if doc_type else ""),
            },
        )

        process_document(document.id)
        messages.success(request, "Documento cargado correctamente (estado borrador).")
        return redirect("documents_drafts")

    else:
        form = DocumentUploadForm()

    return render(request, "documents/upload.html", {"form": form})


@staff_member_required
def drafts_list(request):
    qs = (
        Document.objects
        .select_related("document_type", "created_by")
        .filter(status=Document.Status.DRAFT)
        .order_by("-created_at")
    )
    paginator = Paginator(qs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "documents/drafts_list.html", {"documents": page_obj})


@staff_member_required
def delete_document(request, pk: int):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    doc = get_object_or_404(Document, pk=pk)

    for version in doc.versions.all():
        if version.file:
            version.file.delete(save=False)

    doc.delete()
    messages.success(request, "Documento eliminado correctamente.")
    return redirect("documents_drafts")


@staff_member_required
def review_document(request, pk: int):
    doc = get_object_or_404(
        Document.objects.select_related("document_type", "created_by", "suggested_type").prefetch_related("versions"),
        pk=pk,
    )
    meta, _ = DocumentMetadata.objects.get_or_create(document=doc)
    latest_version = doc.versions.first()

    if request.method == "GET":
        form = DocumentReviewForm(initial={
            "title": doc.title,
            "document_type": doc.document_type_id,
            "enabled": doc.enabled,
            "parties": meta.parties,
            "reference_number": meta.reference_number,
            "date_main": meta.date_main,
            "date_start": meta.date_start,
            "date_end": meta.date_end,
            "amount": meta.amount,
            "notes": meta.notes,
        })
        return render(request, "documents/review.html", {
            "doc": doc,
            "meta": meta,
            "latest_version": latest_version,
            "form": form,
        })

    form = DocumentReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Revisa los campos: hay datos inválidos.")
        return render(request, "documents/review.html", {
            "doc": doc,
            "meta": meta,
            "latest_version": latest_version,
            "form": form,
        })

    from documents.services.audit import log_event
    from documents.models import AuditAction

    prev_enabled = doc.enabled
    form.apply_to_models(doc, meta)
    if prev_enabled != doc.enabled:
        log_event(
            request=request,
            action=AuditAction.ENABLE if doc.enabled else AuditAction.DISABLE,
            actor=request.user,
            document=doc,
            message="Cambio de habilitación",
            metadata={"enabled": doc.enabled},
        )
    meta.save()

    action = request.POST.get("action") or "save"

    if action == "validate":
        doc.status = Document.Status.VALIDATED
        messages.success(request, "Documento validado correctamente.")
    elif action == "publish":
        doc.status = Document.Status.PUBLISHED
        messages.success(request, "Documento publicado. Ya es visible para usuarios.")
    else:
        messages.success(request, "Cambios guardados.")

    doc.save()

    if action == "validate":
        log_event(
            request=request,
            action=AuditAction.VALIDATE,
            actor=request.user,
            document=doc,
            message="Documento validado",
        )
    elif action == "publish":
        log_event(
            request=request,
            action=AuditAction.PUBLISH,
            actor=request.user,
            document=doc,
            message="Documento publicado",
        )
    else:
        log_event(
            request=request,
            action=AuditAction.REVIEW_SAVE,
            actor=request.user,
            document=doc,
            message="Revisión guardada",
        )

    return redirect("document_review", pk=doc.pk)
from .models import Document, DocumentMetadata
from .forms_review import DocumentReviewForm
