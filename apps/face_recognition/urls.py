from django.urls import path
from . import views

app_name = "face"

urlpatterns = [
    path("kiosk/",                    views.kiosk,          name="kiosk"),
    path("profiles/",                 views.profiles_list,  name="profiles"),
    path("register/<int:employee_id>/",views.register_face, name="register"),
    path("delete/<int:employee_id>/", views.delete_face,    name="delete"),
    path("logs/",                     views.scan_logs,      name="logs"),
    # JSON API
    path("api/register/", views.api_register, name="api_register"),
    path("api/verify/",   views.api_verify,   name="api_verify"),
]
