from django.contrib import admin

from .models import EmployeeDocument


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "employee", "category", "uploaded_by", "created_at")
    list_filter = ("category",)
    search_fields = ("employee__employee_id", "title")
    autocomplete_fields = ("employee",)
