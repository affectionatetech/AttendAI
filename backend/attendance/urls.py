from django.urls import path

from .views import (
    CourseDetailView,
    CourseListCreateView,
    EnrollmentDeleteView,
    EnrollmentListCreateView,
    SessionDetailView,
    SessionListCreateView,
    StudentCheckInCompleteView,
    StudentCheckInStartView,
    AttendanceHistoryView,
    AttendanceCSVReportView,
    DashboardSummaryView,
    FraudAlertListView,
    FraudAlertReviewView,
)


urlpatterns = [
    path("courses/", CourseListCreateView.as_view(), name="course-list-create"),
    path("courses/<uuid:pk>/", CourseDetailView.as_view(), name="course-detail"),
    path("enrollments/", EnrollmentListCreateView.as_view(), name="enrollment-list-create"),
    path("enrollments/<uuid:pk>/", EnrollmentDeleteView.as_view(), name="enrollment-delete"),
    path("sessions/", SessionListCreateView.as_view(), name="session-list-create"),
    path("sessions/<uuid:pk>/", SessionDetailView.as_view(), name="session-detail"),
    path("sessions/<uuid:session_id>/check-in/start/", StudentCheckInStartView.as_view(), name="check-in-start"),
    path("attendance/<uuid:attendance_id>/check-in/complete/", StudentCheckInCompleteView.as_view(), name="check-in-complete"),
    path("attendance/history/", AttendanceHistoryView.as_view(), name="attendance-history"),
    path("fraud-alerts/", FraudAlertListView.as_view(), name="fraud-alert-list"),
    path("fraud-alerts/<uuid:alert_id>/review/", FraudAlertReviewView.as_view(), name="fraud-alert-review"),
    path("dashboard/summary/", DashboardSummaryView.as_view(), name="dashboard-summary"),
    path("reports/attendance.csv", AttendanceCSVReportView.as_view(), name="attendance-csv-report"),
]
