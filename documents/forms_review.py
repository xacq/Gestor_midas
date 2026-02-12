from django import forms
from .models import Document, DocumentMetadata, DocumentType


class DocumentReviewForm(forms.Form):
    title = forms.CharField(
        label="Título",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    document_type = forms.ModelChoiceField(
        label="Tipo oficial",
        queryset=DocumentType.objects.filter(is_active=True),
        widget=forms.Select(attrs={"class": "form-select"})
    )

    enabled = forms.BooleanField(
        label="Habilitado",
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    # Metadatos
    parties = forms.CharField(
        label="Partes",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )
    reference_number = forms.CharField(
        label="Referencia / Nº",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    date_main = forms.DateField(
        label="Fecha principal",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    date_start = forms.DateField(
        label="Fecha inicio",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    date_end = forms.DateField(
        label="Fecha fin",
        required=False,
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"})
    )
    amount = forms.DecimalField(
        label="Monto",
        required=False,
        max_digits=14,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01"})
    )
    notes = forms.CharField(
        label="Notas",
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3})
    )

    def apply_to_models(self, doc: Document, meta: DocumentMetadata):
        doc.title = (self.cleaned_data.get("title") or "").strip()
        doc.document_type = self.cleaned_data["document_type"]
        doc.enabled = bool(self.cleaned_data.get("enabled"))

        meta.parties = self.cleaned_data.get("parties") or ""
        meta.reference_number = self.cleaned_data.get("reference_number") or ""
        meta.date_main = self.cleaned_data.get("date_main")
        meta.date_start = self.cleaned_data.get("date_start")
        meta.date_end = self.cleaned_data.get("date_end")
        meta.amount = self.cleaned_data.get("amount")
        meta.notes = self.cleaned_data.get("notes") or ""
