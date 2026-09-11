import datetime

from django.db import IntegrityError
from django.test import TestCase

from apps.departments.models import Department
from apps.employees.models import Employee

from .models import Attendance
from .services import attendance_rate, expected_working_days


def make_employee(employee_id="EMP-TEST-01"):
    dept = Department.objects.create(name=f"Dept for {employee_id}", code=f"D-{employee_id}")
    return Employee.objects.create(
        employee_id=employee_id, first_name="Test", last_name="User",
        email=f"{employee_id.lower()}@example.com", department=dept,
        date_joined_org=datetime.date(2024, 1, 1),
    )


class ExpectedWorkingDaysTests(TestCase):
    def test_excludes_weekends_by_default(self):
        # Monday 2026-01-05 through Sunday 2026-01-11 -> 5 weekdays
        start = datetime.date(2026, 1, 5)
        end = datetime.date(2026, 1, 11)
        self.assertEqual(expected_working_days(start, end), 5)

    def test_single_day_weekday(self):
        self.assertEqual(expected_working_days(datetime.date(2026, 1, 5), datetime.date(2026, 1, 5)), 1)

    def test_single_day_weekend(self):
        self.assertEqual(expected_working_days(datetime.date(2026, 1, 10), datetime.date(2026, 1, 10)), 0)


class AttendanceRateTests(TestCase):
    def test_rate_calculation(self):
        employee = make_employee()
        # Mark 4 of 5 weekdays present in a full week
        for day in [5, 6, 7, 8]:  # Mon-Thu
            Attendance.objects.create(employee=employee, date=datetime.date(2026, 1, day), status="PRESENT")
        Attendance.objects.create(employee=employee, date=datetime.date(2026, 1, 9), status="ABSENT")  # Friday

        result = attendance_rate(employee, datetime.date(2026, 1, 5), datetime.date(2026, 1, 11))
        self.assertEqual(result["expected_working_days"], 5)
        self.assertEqual(result["present_days"], 4)
        self.assertEqual(result["attendance_rate"], 80.0)

    def test_no_expected_days_returns_none_rate(self):
        employee = make_employee("EMP-TEST-02")
        result = attendance_rate(employee, datetime.date(2026, 1, 10), datetime.date(2026, 1, 11))  # weekend only
        self.assertEqual(result["expected_working_days"], 0)
        self.assertIsNone(result["attendance_rate"])


class AttendanceDuplicatePreventionTests(TestCase):
    def test_duplicate_record_raises_integrity_error(self):
        employee = make_employee("EMP-TEST-03")
        Attendance.objects.create(employee=employee, date=datetime.date(2026, 1, 5), status="PRESENT")
        with self.assertRaises(IntegrityError):
            Attendance.objects.create(employee=employee, date=datetime.date(2026, 1, 5), status="ABSENT")
