from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_hub, name="hub"),
    path("employees-by-department/", views.employees_by_department, name="employees_by_department"),
    path("employees-by-status/", views.employees_by_status, name="employees_by_status"),
    path("leave-utilization/", views.leave_utilization, name="leave_utilization"),
    path("performance-completion/", views.performance_review_completion, name="performance_completion"),
    path("employees/export.csv", views.employee_list_export_csv, name="employees_csv"),
]
