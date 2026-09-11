from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class MIUUserAdmin(UserAdmin):
    list_display = ("username", "email", "role", "is_locked", "is_active", "is_staff")
    list_filter = ("role", "is_locked", "is_active", "is_staff")
    fieldsets = UserAdmin.fieldsets + (
        ("MIU Role & Security", {"fields": ("role", "is_locked", "must_change_password", "last_login_ip", "failed_login_attempts")}),
    )
