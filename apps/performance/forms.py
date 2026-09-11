from django import forms

from .models import PerformanceCriterion, PerformanceEvaluation, PerformanceScore


class SelfAssessmentForm(forms.ModelForm):
    class Meta:
        model = PerformanceEvaluation
        fields = ["self_assessment_comment"]
        widgets = {"self_assessment_comment": forms.Textarea(attrs={"rows": 5, "class": "form-control"})}


class SupervisorAssessmentForm(forms.ModelForm):
    class Meta:
        model = PerformanceEvaluation
        fields = ["supervisor_comment"]
        widgets = {"supervisor_comment": forms.Textarea(attrs={"rows": 5, "class": "form-control"})}


class PerformanceScoreForm(forms.ModelForm):
    class Meta:
        model = PerformanceScore
        fields = ["criterion", "score", "comment"]
        widgets = {
            "criterion": forms.Select(attrs={"class": "form-select"}),
            "score": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 5}),
            "comment": forms.TextInput(attrs={"class": "form-control"}),
        }


PerformanceScoreFormSet = forms.modelformset_factory(
    PerformanceScore, form=PerformanceScoreForm, extra=0, can_delete=False,
)
