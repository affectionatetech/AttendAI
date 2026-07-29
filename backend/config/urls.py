from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(_request):
    return JsonResponse({"status": "healthy", "service": "AttendAI API", "version": "0.1.0"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("health/", health_check),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/attendance/", include("attendance.urls")),
]
