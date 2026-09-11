import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.departments.models import Department
from apps.employees.models import Employee

from .models import PerformanceCriterion, PerformanceCycle, PerformanceEvaluation, PerformanceScore
from .services import calculate_final_score, finalize_evaluation


def make_employee():
    dept = Department.objects.create(name="Perf Test Dept", code="PTD")
    return Employee.objects.create(
        employee_id="EMP-PERF-01", first_name="Perf", last_name="Tester",
        email="perf.tester@example.com", department=dept,
        date_joined_org=datetime.date(2024, 1, 1),
    )


class WeightedScoreTests(TestCase):
    def setUp(self):
        self.employee = make_employee()
        self.cycle = PerformanceCycle.objects.create(
            name="Test Cycle", start_date=datetime.date(2026, 1, 1), end_date=datetime.date(2026, 6, 30),
        )
        self.quality = PerformanceCriterion.objects.create(cycle=self.cycle, name="Quality", weight=2)
        self.teamwork = PerformanceCriterion.objects.create(cycle=self.cycle, name="Teamwork", weight=1)
        self.evaluation = PerformanceEvaluation.objects.create(
            cycle=self.cycle, employee=self.employee, stage="SUPERVISOR_ASSESSED",
        )

    def test_weighted_average_calculation(self):
        PerformanceScore.objects.create(evaluation=self.evaluation, criterion=self.quality, score=5)
        PerformanceScore.objects.create(evaluation=self.evaluation, criterion=self.teamwork, score=2)
        # (5*2 + 2*1) / 3 = 12/3 = 4.0
        self.assertEqual(calculate_final_score(self.evaluation), Decimal("4.00"))

    def test_finalize_sets_score_and_stage(self):
        PerformanceScore.objects.create(evaluation=self.evaluation, criterion=self.quality, score=4)
        PerformanceScore.objects.create(evaluation=self.evaluation, criterion=self.teamwork, score=4)
        finalize_evaluation(self.evaluation)
        self.evaluation.refresh_from_db()
        self.assertEqual(self.evaluation.stage, "FINALIZED")
        self.assertEqual(self.evaluation.final_score, Decimal("4.00"))
        self.assertIsNotNone(self.evaluation.finalized_at)

    def test_finalize_requires_supervisor_assessed_stage(self):
        self.evaluation.stage = "OPEN"
        self.evaluation.save()
        with self.assertRaises(ValueError):
            finalize_evaluation(self.evaluation)

    def test_finalized_evaluation_content_is_immutable(self):
        PerformanceScore.objects.create(evaluation=self.evaluation, criterion=self.quality, score=4)
        finalize_evaluation(self.evaluation)
        self.evaluation.refresh_from_db()

        self.evaluation.supervisor_comment = "Trying to sneak an edit in"
        with self.assertRaises(ValidationError):
            self.evaluation.save()
