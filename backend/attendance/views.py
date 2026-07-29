import csv

from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, response, status, views

from accounts.models import User
from .fraud_service import calculate_fraud_risk, create_alert
from .models import AttendanceRecord, ClassSession, Course, Enrollment, FraudAlert, LocationLog
from .permissions import CourseAccessPermission, LecturerOwnsCourseOrAdmin
from .serializers import (
    AttendanceRecordSerializer,
    ClassSessionSerializer,
    CourseSerializer,
    EnrollmentSerializer,
    FraudAlertSerializer,
    FraudReviewSerializer,
    LocationReadingSerializer,
    write_audit_log,
)
from .services import validate_location


class CourseListCreateView(generics.ListCreateAPIView):
    serializer_class = CourseSerializer
    permission_classes = [CourseAccessPermission]

    def get_queryset(self):
        user = self.request.user
        queryset = Course.objects.select_related("lecturer").prefetch_related("students")
        if user.role == User.Role.ADMIN:
            return queryset.order_by("code")
        if user.role == User.Role.LECTURER:
            return queryset.filter(lecturer=user).order_by("code")
        return queryset.filter(students=user).order_by("code")

    def perform_create(self, serializer):
        course = serializer.save()
        write_audit_log(self.request.user, "course_created", course)


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CourseSerializer
    permission_classes = [CourseAccessPermission]
    queryset = Course.objects.select_related("lecturer").prefetch_related("students")

    def perform_update(self, serializer):
        course = serializer.save()
        write_audit_log(self.request.user, "course_updated", course)

    def perform_destroy(self, instance):
        write_audit_log(self.request.user, "course_deleted", instance)
        instance.delete()


class EnrollmentListCreateView(generics.ListCreateAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [LecturerOwnsCourseOrAdmin]

    def get_queryset(self):
        queryset = Enrollment.objects.select_related("student", "course")
        if self.request.user.role == User.Role.LECTURER:
            queryset = queryset.filter(course__lecturer=self.request.user)
        course_id = self.request.query_params.get("course")
        return queryset.filter(course_id=course_id) if course_id else queryset

    def perform_create(self, serializer):
        enrollment = serializer.save()
        write_audit_log(self.request.user, "student_enrolled", enrollment)


class EnrollmentDeleteView(generics.DestroyAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [LecturerOwnsCourseOrAdmin]

    def get_queryset(self):
        queryset = Enrollment.objects.all()
        if self.request.user.role == User.Role.LECTURER:
            queryset = queryset.filter(course__lecturer=self.request.user)
        return queryset

    def perform_destroy(self, instance):
        write_audit_log(self.request.user, "student_unenrolled", instance)
        instance.delete()


class SessionListCreateView(generics.ListCreateAPIView):
    serializer_class = ClassSessionSerializer
    permission_classes = [CourseAccessPermission]

    def get_queryset(self):
        user = self.request.user
        queryset = ClassSession.objects.select_related("course", "course__lecturer")
        if user.role == User.Role.ADMIN:
            pass
        elif user.role == User.Role.LECTURER:
            queryset = queryset.filter(course__lecturer=user)
        else:
            queryset = queryset.filter(course__students=user)
        course_id = self.request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        return queryset.order_by("-starts_at").distinct()

    def perform_create(self, serializer):
        class_session = serializer.save()
        write_audit_log(self.request.user, "session_created", class_session)


class SessionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ClassSessionSerializer
    permission_classes = [CourseAccessPermission]
    queryset = ClassSession.objects.select_related("course", "course__lecturer")

    def perform_update(self, serializer):
        class_session = serializer.save()
        write_audit_log(self.request.user, "session_updated", class_session)

    def perform_destroy(self, instance):
        write_audit_log(self.request.user, "session_deleted", instance)
        instance.delete()


class StudentCheckInStartView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, session_id):
        if request.user.role != User.Role.STUDENT:
            return response.Response(
                {"detail": "Only students can check in."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = LocationReadingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        class_session = get_object_or_404(
            ClassSession.objects.select_related("course"), id=session_id
        )

        if not Enrollment.objects.filter(student=request.user, course=class_session.course).exists():
            return response.Response(
                {"detail": "You are not enrolled in this course."},
                status=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()
        if now < class_session.starts_at or now > class_session.ends_at:
            return response.Response(
                {"detail": "The attendance window is not active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if AttendanceRecord.objects.filter(student=request.user, session=class_session).exists():
            return response.Response(
                {"detail": "An attendance attempt already exists for this session."},
                status=status.HTTP_409_CONFLICT,
            )

        reading = serializer.validated_data
        validation = validate_location(class_session, **{
            "latitude": reading["latitude"],
            "longitude": reading["longitude"],
            "accuracy_metres": reading["accuracy_metres"],
        })

        if not validation["is_accurate"]:
            record_status = AttendanceRecord.Status.REJECTED
            reason = "Location accuracy is too low. Enable precise location and try again."
        elif not validation["is_within_geofence"]:
            record_status = AttendanceRecord.Status.REJECTED
            reason = "Check-in rejected because the device is outside the approved class area."
        else:
            record_status = AttendanceRecord.Status.PENDING_REVIEW
            reason = "Initial location accepted. Complete the dwell verification."

        try:
            attendance = AttendanceRecord.objects.create(
                student=request.user,
                session=class_session,
                status=record_status,
                decision_reason=reason,
            )
        except IntegrityError:
            return response.Response(
                {"detail": "An attendance attempt already exists for this session."},
                status=status.HTTP_409_CONFLICT,
            )

        LocationLog.objects.create(
            attendance=attendance,
            latitude=reading["latitude"],
            longitude=reading["longitude"],
            accuracy_metres=reading["accuracy_metres"],
            distance_metres=validation["distance_metres"],
            is_within_geofence=validation["is_within_geofence"],
            device_identifier=reading["device_identifier"],
            reading_type="initial",
        )
        write_audit_log(request.user, "check_in_started", attendance)
        result = AttendanceRecordSerializer(attendance).data
        result["required_dwell_seconds"] = class_session.minimum_dwell_seconds
        return response.Response(result, status=status.HTTP_201_CREATED)


class StudentCheckInCompleteView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, attendance_id):
        if request.user.role != User.Role.STUDENT:
            return response.Response(
                {"detail": "Only students can complete a check-in."},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = LocationReadingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        attendance = get_object_or_404(
            AttendanceRecord.objects.select_related("session", "session__course"),
            id=attendance_id,
            student=request.user,
        )
        if attendance.status != AttendanceRecord.Status.PENDING_REVIEW:
            return response.Response(
                {"detail": "This attendance attempt cannot be completed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        initial_log = attendance.location_logs.filter(reading_type="initial").first()
        elapsed_seconds = (timezone.now() - initial_log.captured_at).total_seconds()
        if elapsed_seconds < attendance.session.minimum_dwell_seconds:
            remaining = int(attendance.session.minimum_dwell_seconds - elapsed_seconds) + 1
            return response.Response(
                {"detail": "Minimum dwell time has not been reached.", "remaining_seconds": remaining},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if timezone.now() > attendance.session.ends_at:
            attendance.status = AttendanceRecord.Status.REJECTED
            attendance.decision_reason = "The class attendance window ended before verification was completed."
            attendance.save(update_fields=("status", "decision_reason"))
            return response.Response(AttendanceRecordSerializer(attendance).data)

        reading = serializer.validated_data
        validation = validate_location(
            attendance.session,
            reading["latitude"],
            reading["longitude"],
            reading["accuracy_metres"],
        )
        LocationLog.objects.create(
            attendance=attendance,
            latitude=reading["latitude"],
            longitude=reading["longitude"],
            accuracy_metres=reading["accuracy_metres"],
            distance_metres=validation["distance_metres"],
            is_within_geofence=validation["is_within_geofence"],
            device_identifier=reading["device_identifier"],
            reading_type="dwell_confirmation",
        )

        if not validation["is_accurate"]:
            attendance.status = AttendanceRecord.Status.REJECTED
            attendance.decision_reason = "Final location accuracy was too low."
        elif not validation["is_within_geofence"]:
            attendance.status = AttendanceRecord.Status.REJECTED
            attendance.decision_reason = "The device left the approved class area during dwell verification."
        else:
            assessment = calculate_fraud_risk(attendance, initial_log, attendance.location_logs.get(reading_type="dwell_confirmation"))
            attendance.risk_score = assessment["risk_score"]
            if assessment["requires_review"]:
                attendance.status = AttendanceRecord.Status.PENDING_REVIEW
                attendance.decision_reason = "Attendance requires human review: " + " ".join(assessment["reasons"])
                create_alert(attendance, assessment)
            else:
                attendance.status = AttendanceRecord.Status.CONFIRMED
                attendance.decision_reason = "Attendance confirmed after time, location, dwell, and fraud-risk verification."
        attendance.save(update_fields=("status", "risk_score", "decision_reason"))
        write_audit_log(request.user, "check_in_completed", attendance)
        return response.Response(AttendanceRecordSerializer(attendance).data)


class AttendanceHistoryView(generics.ListAPIView):
    serializer_class = AttendanceRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = AttendanceRecord.objects.select_related(
            "student", "session", "session__course"
        ).prefetch_related("location_logs")
        user = self.request.user
        if user.role == User.Role.STUDENT:
            queryset = queryset.filter(student=user)
        elif user.role == User.Role.LECTURER:
            queryset = queryset.filter(session__course__lecturer=user)
        session_id = self.request.query_params.get("session")
        if session_id:
            queryset = queryset.filter(session_id=session_id)
        return queryset.order_by("-checked_in_at")


class FraudAlertListView(generics.ListAPIView):
    serializer_class = FraudAlertSerializer
    permission_classes = [LecturerOwnsCourseOrAdmin]

    def get_queryset(self):
        queryset = FraudAlert.objects.select_related(
            "attendance__student", "attendance__session__course", "reviewed_by"
        )
        if self.request.user.role == User.Role.LECTURER:
            queryset = queryset.filter(attendance__session__course__lecturer=self.request.user)
        review_status = self.request.query_params.get("status")
        if review_status:
            queryset = queryset.filter(review_status=review_status)
        return queryset.order_by("-created_at")


class FraudAlertReviewView(views.APIView):
    permission_classes = [LecturerOwnsCourseOrAdmin]

    @transaction.atomic
    def post(self, request, alert_id):
        queryset = FraudAlert.objects.select_related("attendance", "attendance__session__course")
        if request.user.role == User.Role.LECTURER:
            queryset = queryset.filter(attendance__session__course__lecturer=request.user)
        alert = get_object_or_404(queryset, id=alert_id)
        if alert.review_status != FraudAlert.ReviewStatus.OPEN:
            return response.Response(
                {"detail": "This alert has already been reviewed."},
                status=status.HTTP_409_CONFLICT,
            )
        serializer = FraudReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decision = serializer.validated_data["decision"]
        alert.review_status = decision
        alert.review_note = serializer.validated_data["review_note"]
        alert.reviewed_by = request.user
        alert.reviewed_at = timezone.now()
        alert.save(update_fields=("review_status", "review_note", "reviewed_by", "reviewed_at"))

        attendance = alert.attendance
        if decision == FraudAlert.ReviewStatus.APPROVED:
            attendance.status = AttendanceRecord.Status.CONFIRMED
            attendance.decision_reason = "Attendance confirmed following authorised human review."
        else:
            attendance.status = AttendanceRecord.Status.REJECTED
            attendance.decision_reason = "Attendance rejected following authorised human review."
        attendance.save(update_fields=("status", "decision_reason"))
        write_audit_log(request.user, f"fraud_alert_{decision}", alert)
        return response.Response(FraudAlertSerializer(alert).data)


class DashboardSummaryView(views.APIView):
    permission_classes = [LecturerOwnsCourseOrAdmin]

    def get(self, request):
        attendance = AttendanceRecord.objects.all()
        alerts = FraudAlert.objects.all()
        courses = Course.objects.all()
        sessions = ClassSession.objects.all()
        if request.user.role == User.Role.LECTURER:
            attendance = attendance.filter(session__course__lecturer=request.user)
            alerts = alerts.filter(attendance__session__course__lecturer=request.user)
            courses = courses.filter(lecturer=request.user)
            sessions = sessions.filter(course__lecturer=request.user)
        status_counts = {item["status"]: item["total"] for item in attendance.values("status").annotate(total=Count("id"))}
        return response.Response(
            {
                "courses": courses.count(),
                "sessions": sessions.count(),
                "attendance_total": attendance.count(),
                "confirmed": status_counts.get(AttendanceRecord.Status.CONFIRMED, 0),
                "rejected": status_counts.get(AttendanceRecord.Status.REJECTED, 0),
                "pending_review": status_counts.get(AttendanceRecord.Status.PENDING_REVIEW, 0),
                "open_fraud_alerts": alerts.filter(review_status=FraudAlert.ReviewStatus.OPEN).count(),
            }
        )


class AttendanceCSVReportView(views.APIView):
    permission_classes = [LecturerOwnsCourseOrAdmin]

    def get(self, request):
        records = AttendanceRecord.objects.select_related("student", "session__course")
        if request.user.role == User.Role.LECTURER:
            records = records.filter(session__course__lecturer=request.user)
        course_id = request.query_params.get("course")
        session_id = request.query_params.get("session")
        if course_id:
            records = records.filter(session__course_id=course_id)
        if session_id:
            records = records.filter(session_id=session_id)

        report = HttpResponse(content_type="text/csv")
        report["Content-Disposition"] = 'attachment; filename="attendance-report.csv"'
        writer = csv.writer(report)
        writer.writerow(("Student", "Matric Number", "Course", "Session", "Check-in Time", "Status", "Risk Score", "Decision Reason"))
        for record in records.order_by("session__course__code", "student__full_name"):
            writer.writerow((
                record.student.full_name,
                record.student.matric_number,
                record.session.course.code,
                record.session.title,
                record.checked_in_at.isoformat(),
                record.status,
                record.risk_score,
                record.decision_reason,
            ))
        write_audit_log(request.user, "attendance_report_exported", request.user)
        return report
