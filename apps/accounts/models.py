from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.permissions import Roles


class User(AbstractUser):
    """
    Custom user model. Authentication itself is handled entirely by
    Django's built-in auth framework (per spec: "do not build a custom
    authentication system unnecessarily") — this only adds the role
    field RBAC depends on, plus light account-security metadata.
    """
    role = models.CharField(max_length=20, choices=Roles.CHOICES, default=Roles.EMPLOYEE)
    is_locked = models.BooleanField(
        default=False,
        help_text="Set by an administrator to block sign-in without deleting the account.",
    )
    must_change_password = models.BooleanField(
        default=False,
        help_text="Forces a password change on next login (e.g. after admin-issued reset).",
    )
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    failed_login_attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "accounts_user"

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_admin_role(self):
        return self.role == Roles.ADMIN or self.is_superuser

    @property
    def is_hr(self):
        return self.role == Roles.HR

    @property
    def is_department_head(self):
        return self.role == Roles.DEPARTMENT_HEAD

    @property
    def is_employee_role(self):
        return self.role == Roles.EMPLOYEE

    @property
    def is_management(self):
        return self.role == Roles.MANAGEMENT
