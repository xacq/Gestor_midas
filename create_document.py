
import os
import django
from django.core.files import File
from django.contrib.auth import get_user_model
from documents.models import Document, DocumentType, DocumentVersion

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

User = get_user_model()

def create_document(file_path, title, document_type_name, username):
    # Get user
    user = User.objects.get(username=username)

    # Get document type
    doc_type = DocumentType.objects.get(name=document_type_name)

    # Create document
    doc = Document.objects.create(
        title=title,
        document_type=doc_type,
        uploaded_by=user,
    )

    # Create document version
    with open(file_path, 'rb') as f:
        version = DocumentVersion.objects.create(
            document=doc,
            file=File(f, name=os.path.basename(file_path)),
            uploaded_by=user,
        )

    print(f"Document created with ID: {doc.id}")
    return doc.id

if __name__ == '__main__':
    file_to_upload = 'ejemplos/prueba1.pdf'
    doc_id = create_document(file_to_upload, 'Test Document 1', 'Contrato', 'ivodoria')
    print(f"Successfully created document with id {doc_id}")
