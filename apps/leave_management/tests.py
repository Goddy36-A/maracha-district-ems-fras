import datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.permissions import Roles
from apps.departments.models import Department
from apps.employees.models import Employee

from . import services
from .models import LeaveBalance, LeaveType

User = get_user_model()


def make_employee():
    dept = Department.objects.create(name="Leave Test Dept", code="LTD")
    return Employee.objects.create(
        employee_id="EMP-LEAVE-01", first_name="Leave", last_name="Tester",
        email="leave.tester@example.com", department=dept,
        date_joined_org=datetime.date(2024, 1, 1),
    )


class LeaveWorkflowTests(TestCase):
    def setUp(self):
        self.employee = make_employee()
        self.leave_type = LeaveType.objects.create(name="Annual Leave", default_annual_days=21, requires_hr_review=True)
        self.dept_head = User.objects.create_user(username="depthead", password="x", role=Roles.DEPARTMENT_HEAD)
        self.hr = User.objects.create_user(username="hr", password="x", role=Roles.HR)

    def test_submit_creates_pending_request_and_pending_balance(self):
        req = services.submit_leave_request(
            self.employee, self.leave_type,
            datetime.date(2026, 2, 2), datetime.date(2026, 2, 4), "Vacation",
        )
        self.assertEqual(req.status, "PENDING")
        self.assertEqual(req.number_of_days, 3)
        balance = LeaveBalance.objects.get(employee=self.employee, leave_type=self.leave_type, year=2026)
        self.assertEqual(balance.pending, 3)
        self.assertEqual(balance.used, 0)

    def test_full_approval_chain_moves_pending_to_used(self):
        req = services.submit_leave_request(
            self.employee, self.leave_type,
            datetime.date(2026, 2, 2), datetime.date(2026, 2, 4), "Vacation",
        )
        services.department_approve(req, approver=self.dept_head)
        req.refresh_from_db()
        self.assertEqual(req.status, "DEPT_APPROVED")

        services.hr_review(req, reviewer=self.hr, approve=True)
        req.refresh_from_db()
        self.assertEqual(req.status, "APPROVED")

        balance = LeaveBalance.objects.get(employee=self.employee, leave_type=self.leave_type, year=2026)
        self.assertEqual(balance.used, 3)
        self.assertEqual(balance.pending, 0)

    def test_hr_rejection_releases_pending_balance(self):
        req = services.submit_leave_request(
            self.employee, self.leave_type,
            datetime.date(2026, 2, 2), datetime.date(2026, 2, 4), "Vacation",
        )
        services.department_approve(req, approver=self.dept_head)
        services.hr_review(req, reviewer=self.hr, approve=False, comment="Insufficient staffing")
        req.refresh_from_db()
        self.assertEqual(req.status, "REJECTED")

        balance = LeaveBalance.objects.get(employee=self.employee, leave_type=self.leave_type, year=2026)
        self.assertEqual(balance.used, 0)
        self.assertEqual(balance.pending, 0)

    def test_cannot_hr_review_before_department_approval(self):
        req = services.submit_leave_request(
            self.employee, self.leave_type,
            datetime.date(2026, 2, 2), datetime.date(2026, 2, 4), "Vacation",
        )
        with self.assertRaises(ValidationError):
            services.hr_review(req, reviewer=self.hr, approve=True)

    def test_cancel_only_allowed_before_final_decision(self):
        req = services.submit_leave_request(
            self.employee, self.leave_type,
            datetime.date(2026, 2, 2), datetime.date(2026, 2, 4), "Vacation",
        )
        services.department_approve(req, approver=self.dept_head)
        services.hr_review(req, reviewer=self.hr, approve=True)
        with self.assertRaises(ValidationError):
            services.cancel(req)

    def test_end_date_before_start_date_rejected(self):
        with self.assertRaises(ValidationError):
            services.submit_leave_request(
                self.employee, self.leave_type,
                datetime.date(2026, 2, 5), datetime.date(2026, 2, 1), "Bad dates",
            )
