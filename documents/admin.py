from django.contrib import admin
from .models import DocumentType, Document, DocumentVersion, DocumentMetadata


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    fields = ("version_number", "file", "uploaded_by", "uploaded_at")
    readonly_fields = ("uploaded_at",)


class DocumentMetadataInline(admin.StackedInline):
    model = DocumentMetadata
    extra = 0


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "document_type", "status", "enabled", "created_by", "created_at")
    list_filter = ("document_type", "status", "enabled")
    search_fields = ("title", "id")
    readonly_fields = ("created_at", "updated_at")
    inlines = [DocumentMetadataInline, DocumentVersionInline]

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
