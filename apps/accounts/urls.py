from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.MIULoginView.as_view(), name="login"),
    path("logout/", views.MIULogoutView.as_view(), name="logout"),
    path("locked/", views.account_locked_notice, name="account_locked"),

    path("password/change/", views.MIUPasswordChangeView.as_view(), name="password_change"),
    path("password/change/done/", views.MIUPasswordChangeDoneView.as_view(), name="password_change_done"),

    path("password/reset/", views.MIUPasswordResetView.as_view(), name="password_reset"),
    path("password/reset/done/", views.MIUPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("password/reset/confirm/<uidb64>/<token>/", views.MIUPasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("password/reset/complete/", views.MIUPasswordResetCompleteView.as_view(), name="password_reset_complete"),
]
