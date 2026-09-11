from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.home, name="home"),
    path("hr/", views.hr_dashboard, name="hr"),
    path("management/", views.management_dashboard, name="management"),
    path("department-head/", views.department_head_dashboard, name="department_head"),
    path("effectiveness/", views.effectiveness_dashboard, name="effectiveness"),
    path("survey/", views.satisfaction_survey, name="survey"),
]
