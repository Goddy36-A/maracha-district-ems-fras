from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()


class MIULoginForm(AuthenticationForm):
    username = forms.CharField(
        label="Username or Email",
        widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True, "placeholder": "Username or Email"}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
    )

    error_messages = {
        **AuthenticationForm.error_messages,
        "locked": "This account has been locked due to multiple failed sign-in attempts. Contact your administrator.",
    }

    def confirm_login_allowed(self, user):
        if user.is_locked:
            raise forms.ValidationError(self.error_messages["locked"], code="locked")
        super().confirm_login_allowed(user)


class MIUPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Current Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password1 = forms.CharField(
        label="New Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password2 = forms.CharField(
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
