"""
Final Score = Σ(Criterion Score × Criterion Weight) / Σ(Weight)

Normalizing by total weight keeps the result on the same scale as the
raw scores (e.g. still roughly 1-5) rather than an unbounded weighted
sum, while still respecting relative weighting between criteria.
"""
from decimal import Decimal

from django.utils import timezone

from .models import PerformanceEvaluation, PerformanceScore


def calculate_final_score(evaluation: PerformanceEvaluation):
    scores = PerformanceScore.objects.filter(evaluation=evaluation).select_related("criterion")
    total_weight = sum((s.criterion.weight for s in scores), Decimal("0"))
    if total_weight == 0:
        return None
    weighted_sum = sum((Decimal(s.score) * s.criterion.weight for s in scores), Decimal("0"))
    return round(weighted_sum / total_weight, 2)


def finalize_evaluation(evaluation: PerformanceEvaluation):
    if evaluation.stage != "SUPERVISOR_ASSESSED":
        raise ValueError("Only evaluations with a submitted supervisor assessment can be finalized.")
    evaluation.final_score = calculate_final_score(evaluation)
    evaluation.stage = "FINALIZED"
    evaluation.finalized_at = timezone.now()
    evaluation.save(update_fields=["final_score", "stage", "finalized_at"])
    return evaluation


def acknowledge_evaluation(evaluation: PerformanceEvaluation):
    if evaluation.stage != "FINALIZED":
        raise ValueError("Only finalized evaluations can be acknowledged.")
    evaluation.stage = "ACKNOWLEDGED"
    evaluation.employee_acknowledged_at = timezone.now()
    evaluation.save(update_fields=["stage", "employee_acknowledged_at"])
    return evaluation
