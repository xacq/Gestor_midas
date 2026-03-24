DEFAULT_DOCUMENT_TYPES = (
    {"code": "CONTRACT", "name": "Contrato", "description": ""},
    {"code": "PO", "name": "Orden de compra", "description": ""},
    {"code": "CERT", "name": "Certificación", "description": ""},
)


def ensure_default_document_types(document_type_model=None):
    if document_type_model is None:
        from documents.models import DocumentType

        document_type_model = DocumentType

    existing_by_code = document_type_model.objects.in_bulk(
        [item["code"] for item in DEFAULT_DOCUMENT_TYPES],
        field_name="code",
    )

    for item in DEFAULT_DOCUMENT_TYPES:
        obj = existing_by_code.get(item["code"])
        if obj is None:
            document_type_model.objects.create(
                code=item["code"],
                name=item["name"],
                description=item["description"],
                is_active=True,
            )
            continue

        fields_to_update = []
        if obj.name != item["name"]:
            obj.name = item["name"]
            fields_to_update.append("name")
        if obj.description != item["description"]:
            obj.description = item["description"]
            fields_to_update.append("description")
        if not obj.is_active:
            obj.is_active = True
            fields_to_update.append("is_active")

        if fields_to_update:
            obj.save(update_fields=fields_to_update)


def get_active_document_types_queryset(document_type_model=None):
    if document_type_model is None:
        from documents.models import DocumentType

        document_type_model = DocumentType

    ensure_default_document_types(document_type_model=document_type_model)
    return document_type_model.objects.filter(is_active=True).order_by("name")
