from django.urls import path

from . import views

app_name = "performance"

urlpatterns = [
    path("mine/", views.my_evaluations, name="mine"),
    path("<int:pk>/", views.evaluation_detail, name="detail"),
    path("<int:pk>/self-assessment/", views.submit_self_assessment, name="self_assessment"),
    path("<int:pk>/supervisor-assessment/", views.submit_supervisor_assessment, name="supervisor_assessment"),
    path("<int:pk>/finalize/", views.finalize, name="finalize"),
    path("<int:pk>/acknowledge/", views.acknowledge, name="acknowledge"),
]
