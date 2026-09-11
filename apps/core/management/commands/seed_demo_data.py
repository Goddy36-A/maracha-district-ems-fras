"""
Loads clearly-labeled SAMPLE data for local development and demos only.
No real MIU employee records, departments, or statistics are used —
see spec Section 7: "Never fabricate real MIU employee records."
Run with: python manage.py seed_demo_data
"""
import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.permissions import Roles
from apps.departments.models import Department, Position
from apps.employees.models import Employee
from apps.leave_management.models import LeaveType
from apps.performance.models import PerformanceCriterion, PerformanceCycle

User = get_user_model()


class Command(BaseCommand):
    help = "Load clearly-labeled sample/demo data for MIU-EMS (not real institutional data)."

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data (sample/demo only — not real MIU records)...")

        # --- Departments (sample names, not verified MIU units) ---
        dept_names = [
            ("HR-DEMO", "Human Resources (Demo)"),
            ("ICT-DEMO", "Information & Communication Technology (Demo)"),
            ("FIN-DEMO", "Finance (Demo)"),
            ("ACAD-DEMO", "Academic Affairs (Demo)"),
        ]
        departments = {}
        for code, name in dept_names:
            dept, _ = Department.objects.get_or_create(code=code, defaults={"name": name})
            departments[code] = dept

        positions = {}
        for code, dept in departments.items():
            pos, _ = Position.objects.get_or_create(
                title=f"{dept.name} Officer", department=dept,
                defaults={"employment_category": "FULL_TIME"},
            )
            positions[code] = pos

        # --- Leave types (sample entitlements — verify against real policy) ---
        LeaveType.objects.get_or_create(name="Annual Leave", defaults={"default_annual_days": 21})
        LeaveType.objects.get_or_create(name="Sick Leave", defaults={"default_annual_days": 10})
        LeaveType.objects.get_or_create(name="Compassionate Leave", defaults={"default_annual_days": 5})

        # --- Performance cycle + sample criteria ---
        cycle, _ = PerformanceCycle.objects.get_or_create(
            name="2026 Sample Review Cycle",
            defaults={"start_date": datetime.date(2026, 1, 1), "end_date": datetime.date(2026, 6, 30)},
        )
        for name, weight in [("Quality of Work", 2), ("Productivity", 2), ("Teamwork", 1), ("Communication", 1)]:
            PerformanceCriterion.objects.get_or_create(cycle=cycle, name=name, defaults={"weight": weight})

        # --- Demo users, one per role ---
        demo_accounts = [
            ("admin_demo", Roles.ADMIN, "System", "Administrator"),
            ("hr_demo", Roles.HR, "Hope", "Reyes"),
            ("depthead_demo", Roles.DEPARTMENT_HEAD, "Daniel", "Head"),
            ("employee_demo", Roles.EMPLOYEE, "Emma", "Employee"),
            ("management_demo", Roles.MANAGEMENT, "Martin", "Manager"),
        ]

        created_users = {}
        for username, role, first, last in demo_accounts:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@miu-demo.local", "role": role, "first_name": first, "last_name": last},
            )
            if created:
                user.set_password("ChangeMe123!")
                if role == Roles.ADMIN:
                    user.is_staff = True
                user.save()
            created_users[username] = user

        # Link the department-head and employee demo accounts to Employee profiles
        Employee.objects.get_or_create(
            employee_id="MIU-DEMO-001",
            defaults={
                "user": created_users["depthead_demo"],
                "first_name": "Daniel", "last_name": "Head",
                "email": "depthead_demo@miu-demo.local",
                "department": departments["ICT-DEMO"], "position": positions["ICT-DEMO"],
                "date_joined_org": datetime.date(2022, 3, 1),
            },
        )
        departments["ICT-DEMO"].head = Employee.objects.get(employee_id="MIU-DEMO-001")
        departments["ICT-DEMO"].save(update_fields=["head"])

        Employee.objects.get_or_create(
            employee_id="MIU-DEMO-002",
            defaults={
                "user": created_users["employee_demo"],
                "first_name": "Emma", "last_name": "Employee",
                "email": "employee_demo@miu-demo.local",
                "department": departments["ICT-DEMO"], "position": positions["ICT-DEMO"],
                "date_joined_org": datetime.date(2023, 8, 15),
                "supervisor": Employee.objects.get(employee_id="MIU-DEMO-001"),
            },
        )

        self.stdout.write(self.style.SUCCESS(
            "Demo data loaded. Sample login credentials (password: ChangeMe123!):\n"
            "  admin_demo / hr_demo / depthead_demo / employee_demo / management_demo\n"
            "Change these passwords immediately in any shared or deployed environment."
        ))
