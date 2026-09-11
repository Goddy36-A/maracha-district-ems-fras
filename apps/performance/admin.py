from django.contrib import admin

from .models import PerformanceCriterion, PerformanceCycle, PerformanceEvaluation, PerformanceScore


class CriterionInline(admin.TabularInline):
    model = PerformanceCriterion
    extra = 1


@admin.register(PerformanceCycle)
class PerformanceCycleAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date", "is_open")
    inlines = [CriterionInline]


class ScoreInline(admin.TabularInline):
    model = PerformanceScore
    extra = 0


@admin.register(PerformanceEvaluation)
class PerformanceEvaluationAdmin(admin.ModelAdmin):
    list_display = ("employee", "cycle", "stage", "final_score", "finalized_at")
    list_filter = ("stage", "cycle")
    search_fields = ("employee__employee_id", "employee__first_name", "employee__last_name")
    autocomplete_fields = ("employee",)
    inlines = [ScoreInline]
