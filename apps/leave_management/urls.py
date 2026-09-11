from django.urls import path

from . import views

app_name = "leave"

urlpatterns = [
    path("mine/", views.my_leave, name="mine"),
    path("<int:pk>/cancel/", views.cancel_leave, name="cancel"),

    path("department/approvals/", views.department_approvals, name="department_approvals"),
    path("department/approvals/<int:pk>/approve/", views.department_approve_action, name="department_approve"),

    path("hr/review/", views.hr_review_queue, name="hr_review_queue"),
    path("hr/review/<int:pk>/<str:decision>/", views.hr_review_action, name="hr_review_action"),
]
