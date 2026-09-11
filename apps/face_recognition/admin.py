from django.contrib import admin
from .models import FaceProfile, FaceScanLog

@admin.register(FaceProfile)
class FaceProfileAdmin(admin.ModelAdmin):
    list_display  = ["employee", "sample_count", "is_active", "registered_by", "created_at"]
    list_filter   = ["is_active"]
    search_fields = ["employee__first_name", "employee__last_name", "employee__employee_id"]
    readonly_fields = ["created_at", "updated_at"]

@admin.register(FaceScanLog)
class FaceScanLogAdmin(admin.ModelAdmin):
    list_display  = ["created_at", "result", "employee", "distance", "ip_address"]
    list_filter   = ["result"]
    search_fields = ["employee__employee_id"]
    readonly_fields = ["created_at"]
