from django import forms

from .models import Attendance


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["employee", "date", "check_in_time", "check_out_time", "status", "remarks"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "check_in_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "check_out_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "remarks": forms.TextInput(attrs={"class": "form-control"}),
            "employee": forms.Select(attrs={"class": "form-select"}),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def clean(self):
        cleaned = super().clean()
        check_in = cleaned.get("check_in_time")
        check_out = cleaned.get("check_out_time")
        if check_in and check_out and check_out <= check_in:
            raise forms.ValidationError("Check-out time must be after check-in time.")
        return cleaned


class AttendanceFilterForm(forms.Form):
    start_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    end_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    department = forms.CharField(required=False, widget=forms.HiddenInput())
