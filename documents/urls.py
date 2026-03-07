from django.urls import path
from .views_manager import manager_dashboard
from .views_audit import audit_log_list

from .views import (
    published_list,
    document_detail,
    upload_document,
    drafts_list,
    delete_document,
    review_document,  # <-- IMPORTANTE
)

urlpatterns = [
    path("drafts/", drafts_list, name="documents_drafts"),
    path("drafts/<int:pk>/delete/", delete_document, name="document_delete"),
    path("upload/", upload_document, name="upload_document"),
    path("review/<int:pk>/", review_document, name="document_review"),
    path("", published_list, name="documents_list"),
    path("<int:pk>/", document_detail, name="document_detail"),
    path("manager/", manager_dashboard, name="manager_dashboard"),
    path("audit/", audit_log_list, name="audit_log"),
]
