from django.contrib import admin

from .models import EffectivenessIndicator, SatisfactionResponse


@admin.register(EffectivenessIndicator)
class EffectivenessIndicatorAdmin(admin.ModelAdmin):
    list_display = ("indicator_name", "dimension", "period", "value", "unit", "measured_on", "recorded_by")
    list_filter = ("dimension", "period")
    search_fields = ("indicator_name",)


@admin.register(SatisfactionResponse)
class SatisfactionResponseAdmin(admin.ModelAdmin):
    list_display = ("id", "respondent", "mean_score", "submitted_at")
    readonly_fields = ("submitted_at",)
