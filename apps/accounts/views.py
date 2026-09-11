from django.contrib.auth import views as auth_views, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse_lazy

from apps.audit.utils import log_action

from .forms import MIULoginForm, MIUPasswordChangeForm

User = get_user_model()


class MIULoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = MIULoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        ip = self.request.META.get("REMOTE_ADDR")
        self.request.user.last_login_ip = ip
        self.request.user.save(update_fields=["last_login_ip"])
        log_action(
            actor=self.request.user,
            action="USER_LOGIN",
            object_type="User",
            object_id=self.request.user.id,
            request=self.request,
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Invalid credentials, or your account may be locked.")
        return super().form_invalid(form)


class MIULogoutView(LoginRequiredMixin, auth_views.LogoutView):
    next_page = reverse_lazy("accounts:login")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            log_action(
                actor=request.user,
                action="USER_LOGOUT",
                object_type="User",
                object_id=request.user.id,
                request=request,
            )
        return super().dispatch(request, *args, **kwargs)


class MIUPasswordChangeView(LoginRequiredMixin, auth_views.PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = MIUPasswordChangeForm
    success_url = reverse_lazy("accounts:password_change_done")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.must_change_password = False
        self.request.user.save(update_fields=["must_change_password"])
        messages.success(self.request, "Your password has been updated.")
        return response


class MIUPasswordChangeDoneView(LoginRequiredMixin, auth_views.PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"


class MIUPasswordResetView(auth_views.PasswordResetView):
    template_name = "accounts/password_reset.html"
    email_template_name = "accounts/password_reset_email.html"
    subject_template_name = "accounts/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class MIUPasswordResetDoneView(auth_views.PasswordResetDoneView):
    template_name = "accounts/password_reset_done.html"


class MIUPasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class MIUPasswordResetCompleteView(auth_views.PasswordResetCompleteView):
    template_name = "accounts/password_reset_complete.html"


@login_required
def account_locked_notice(request):
    return render(request, "accounts/account_locked.html")
