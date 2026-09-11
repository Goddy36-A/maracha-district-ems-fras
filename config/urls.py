from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    path("accounts/", include("apps.accounts.urls")),
    path("employees/", include("apps.employees.urls")),
    path("attendance/", include("apps.attendance.urls")),
    path("leave/", include("apps.leave_management.urls")),
    path("performance/", include("apps.performance.urls")),
    path("documents/", include("apps.documents.urls")),
    path("reports/", include("apps.reports.urls")),
    path("face/", include("apps.face_recognition.urls")),
    path("", include("apps.dashboard.urls")),
]

handler403 = "apps.core.views.error_403"
handler404 = "apps.core.views.error_404"
handler500 = "apps.core.views.error_500"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
