from django.contrib import admin

from .models import LeaveBalance, LeaveRequest, LeaveType


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "default_annual_days", "requires_hr_review", "is_active")


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ("employee", "leave_type", "start_date", "end_date", "number_of_days", "status")
    list_filter = ("status", "leave_type")
    search_fields = ("employee__employee_id", "employee__first_name", "employee__last_name")
    autocomplete_fields = ("employee",)


@admin.register(LeaveBalance)
class LeaveBalanceAdmin(admin.ModelAdmin):
    list_display = ("employee", "leave_type", "year", "annual_entitlement", "used", "pending", "remaining")
    list_filter = ("leave_type", "year")
    search_fields = ("employee__employee_id",)
    autocomplete_fields = ("employee",)
