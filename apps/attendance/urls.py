from django.urls import path

from . import views

app_name = "attendance"

urlpatterns = [
    path("", views.attendance_list, name="list"),
    path("new/", views.attendance_create, name="create"),
    path("mine/", views.my_attendance, name="mine"),
]
