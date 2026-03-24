from django import forms
from django.core.exceptions import ValidationError
from .models import DocumentType
from .services.document_types import get_active_document_types_queryset


class DocumentUploadForm(forms.Form):
    title = forms.CharField(
        label="Título",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Contrato de arrendamiento 2026"})
    )

    document_type = forms.ModelChoiceField(
        queryset=DocumentType.objects.none(),
        label="Tipo de documento",
        empty_label="Selecciona un tipo",
        widget=forms.Select(attrs={"class": "form-select"})
    )

    file = forms.FileField(
        label="Archivo PDF",
        widget=forms.ClearableFileInput(attrs={"class": "form-control", "accept": "application/pdf"})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["document_type"].queryset = get_active_document_types_queryset()

    def clean_file(self):
        f = self.cleaned_data["file"]
        name = (f.name or "").lower()
        if not name.endswith(".pdf"):
            raise ValidationError("Solo se permiten archivos PDF.")
        return f
