from django.contrib import admin

from .models import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("employee_id", "full_name", "department", "position", "employment_status", "date_joined_org")
    list_filter = ("employment_status", "employment_type", "department")
    search_fields = ("employee_id", "first_name", "last_name", "email")
    autocomplete_fields = ("department", "position", "supervisor", "user")
