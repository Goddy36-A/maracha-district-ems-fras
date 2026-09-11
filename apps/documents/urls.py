from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("upload/", views.document_upload, name="upload"),
    path("<int:pk>/download/", views.document_download, name="download"),
    path("mine/", views.my_documents, name="mine"),
]
