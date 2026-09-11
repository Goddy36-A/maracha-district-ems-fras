import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.permissions import Roles
from apps.departments.models import Department
from apps.employees.models import Employee

User = get_user_model()


class EmployeeAuthorizationTests(TestCase):
    """
    Verifies spec Section 45 ("Authorization Rule"): backend must reject
    unauthorized access even when a request is crafted directly, not
    just when a UI link is hidden.
    """

    def setUp(self):
        self.dept_a = Department.objects.create(name="Dept A", code="DA")
        self.dept_b = Department.objects.create(name="Dept B", code="DB")

        self.employee_a = Employee.objects.create(
            employee_id="EMP-A", first_name="Alice", last_name="A",
            email="alice@example.com", department=self.dept_a,
            date_joined_org=datetime.date(2024, 1, 1),
        )
        self.employee_b = Employee.objects.create(
            employee_id="EMP-B", first_name="Bob", last_name="B",
            email="bob@example.com", department=self.dept_b,
            date_joined_org=datetime.date(2024, 1, 1),
        )

        self.user_a = User.objects.create_user(username="alice", password="x", role=Roles.EMPLOYEE)
        self.employee_a.user = self.user_a
        self.employee_a.save()

        self.hr_user = User.objects.create_user(username="hr", password="x", role=Roles.HR)

    def test_employee_cannot_view_other_employees_record(self):
        self.client.force_login(self.user_a)
        resp = self.client.get(f"/employees/{self.employee_b.pk}/")
        self.assertEqual(resp.status_code, 403)

    def test_employee_can_view_own_record(self):
        self.client.force_login(self.user_a)
        resp = self.client.get(f"/employees/{self.employee_a.pk}/")
        self.assertEqual(resp.status_code, 200)

    def test_unauthenticated_user_redirected_from_employee_list(self):
        resp = self.client.get("/employees/")
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/accounts/login/", resp.url)

    def test_employee_role_forbidden_from_employee_list(self):
        self.client.force_login(self.user_a)
        resp = self.client.get("/employees/")
        self.assertEqual(resp.status_code, 403)

    def test_self_service_form_cannot_alter_employment_status(self):
        self.client.force_login(self.user_a)
        self.client.post(f"/employees/{self.employee_a.pk}/edit/", {
            "phone": "5551234", "address": "New address",
            "employment_status": "TERMINATED",  # not a field on the self-service form
        })
        self.employee_a.refresh_from_db()
        self.assertEqual(self.employee_a.employment_status, "ACTIVE")
        self.assertEqual(self.employee_a.phone, "5551234")

    def test_hr_can_view_any_employee(self):
        self.client.force_login(self.hr_user)
        resp = self.client.get(f"/employees/{self.employee_b.pk}/")
        self.assertEqual(resp.status_code, 200)


class AccountLockoutTests(TestCase):
    def test_account_locks_after_max_failed_attempts(self):
        user = User.objects.create_user(username="locktest", password="correct-horse-battery-staple")
        for _ in range(5):
            self.client.post("/accounts/login/", {"username": "locktest", "password": "wrong"})
        user.refresh_from_db()
        self.assertTrue(user.is_locked)

        # Even the correct password should now fail
        resp = self.client.post("/accounts/login/", {"username": "locktest", "password": "correct-horse-battery-staple"})
        self.assertContains(resp, "locked")
