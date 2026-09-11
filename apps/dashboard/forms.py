from django import forms

LIKERT_CHOICES = [(1, "1 - Strongly Disagree"), (2, "2 - Disagree"), (3, "3 - Neutral"),
                   (4, "4 - Agree"), (5, "5 - Strongly Agree")]

# Sample questions only — NOT official MIU survey instrument (spec Section 56).
QUESTIONS = [
    ("ease_of_use", "The system is easy to use."),
    ("accessibility", "The system makes employee information easier to access."),
    ("workload_reduction", "The system reduces administrative workload."),
    ("data_accuracy", "The system improves accuracy of employee records."),
    ("leave_management", "The system makes leave management easier."),
    ("attendance_management", "The system improves attendance management."),
    ("hr_reporting", "The system improves HR reporting."),
    ("decision_support", "The system supports better decision-making."),
    ("reliability", "The system is reliable."),
    ("overall_satisfaction", "Overall, I am satisfied with the system."),
]


class SatisfactionSurveyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for key, label in QUESTIONS:
            self.fields[key] = forms.TypedChoiceField(
                label=label, choices=LIKERT_CHOICES, coerce=int,
                widget=forms.RadioSelect,
            )

    def as_answers_dict(self):
        return {key: self.cleaned_data[key] for key, _ in QUESTIONS}
