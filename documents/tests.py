from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .forms import DocumentUploadForm
from .forms_review import DocumentReviewForm
from .models import DocumentType
from .services.summarization import summarize_text


class DocumentTypeBootstrapTests(TestCase):
    def test_upload_form_bootstraps_default_document_types(self):
        DocumentType.objects.all().delete()

        form = DocumentUploadForm()

        self.assertEqual(form.fields["document_type"].queryset.count(), 3)
        self.assertTrue(DocumentType.objects.filter(code="CONTRACT", is_active=True).exists())
        self.assertTrue(DocumentType.objects.filter(code="PO", is_active=True).exists())
        self.assertTrue(DocumentType.objects.filter(code="CERT", is_active=True).exists())

    def test_upload_form_accepts_seeded_document_type(self):
        form = DocumentUploadForm()
        document_type = form.fields["document_type"].queryset.get(code="CONTRACT")

        bound_form = DocumentUploadForm(
            data={"title": "Contrato de prueba", "document_type": str(document_type.pk)},
            files={"file": SimpleUploadedFile("contrato.pdf", b"%PDF-1.4 test", content_type="application/pdf")},
        )

        self.assertTrue(bound_form.is_valid(), bound_form.errors.as_json())

    def test_review_form_bootstraps_default_document_types(self):
        DocumentType.objects.all().delete()

        form = DocumentReviewForm()

        self.assertEqual(form.fields["document_type"].queryset.count(), 3)


class SummarizationTests(TestCase):
    def test_summarize_text_returns_longer_text_for_large_input(self):
        sentence = (
            "Este contrato establece obligaciones, plazos, responsables, montos y condiciones "
            "de cumplimiento para las partes involucradas en la adquisicion institucional."
        )
        text = " ".join(f"{sentence} Seccion {index}." for index in range(1, 15))

        summary = summarize_text(text, num_sentences=8)

        self.assertTrue(summary)
        self.assertGreater(len(summary), 600)
