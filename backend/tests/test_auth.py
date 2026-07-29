from rest_framework import status
from rest_framework.test import APITestCase
from django.utils import timezone
from datetime import timedelta

from accounts.models import User
from attendance.models import AttendanceRecord, AuditLog, ClassSession, Course, Enrollment, FraudAlert
from attendance.services import haversine_distance


class AuthenticationTests(APITestCase):
    registration_data = {
        "full_name": "Ada Student",
        "email": "ada@example.com",
        "password": "StrongPass123!",
        "role": "student",
        "matric_number": "STU001",
    }

    def test_health_check(self):
        response = self.client.get("/health/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()["status"], "healthy")

    def test_register_login_and_profile(self):
        registration = self.client.post("/api/v1/auth/register/", self.registration_data, format="json")
        self.assertEqual(registration.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", registration.json())

        login = self.client.post(
            "/api/v1/auth/login/",
            {"email": "ada@example.com", "password": "StrongPass123!"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {login.json()['access']}")
        profile = self.client.get("/api/v1/auth/me/")
        self.assertEqual(profile.status_code, status.HTTP_200_OK)
        self.assertEqual(profile.json()["matric_number"], "STU001")

    def test_admin_self_registration_is_blocked(self):
        payload = self.registration_data | {"role": "admin", "matric_number": None}
        response = self.client.post("/api/v1/auth/register/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CourseManagementTests(APITestCase):
    def setUp(self):
        self.lecturer = User.objects.create_user(
            email="lecturer@example.com",
            password="StrongPass123!",
            full_name="Test Lecturer",
            role=User.Role.LECTURER,
            staff_number="LEC001",
        )
        self.other_lecturer = User.objects.create_user(
            email="other@example.com",
            password="StrongPass123!",
            full_name="Other Lecturer",
            role=User.Role.LECTURER,
            staff_number="LEC002",
        )
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StrongPass123!",
            full_name="Test Student",
            role=User.Role.STUDENT,
            matric_number="STU001",
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_lecturer_creates_own_course_and_audit_log(self):
        self.authenticate(self.lecturer)
        response = self.client.post(
            "/api/v1/attendance/courses/",
            {"code": "CSC401", "title": "Artificial Intelligence"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.get().lecturer, self.lecturer)
        self.assertTrue(AuditLog.objects.filter(action="course_created").exists())

    def test_student_cannot_create_course(self):
        self.authenticate(self.student)
        response = self.client.post(
            "/api/v1/attendance/courses/",
            {"code": "CSC401", "title": "Artificial Intelligence"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lecturer_can_enrol_student_only_in_own_course(self):
        own_course = Course.objects.create(code="CSC401", title="AI", lecturer=self.lecturer)
        other_course = Course.objects.create(code="CSC402", title="Networks", lecturer=self.other_lecturer)
        self.authenticate(self.lecturer)

        valid = self.client.post(
            "/api/v1/attendance/enrollments/",
            {"student": str(self.student.id), "course": str(own_course.id)},
            format="json",
        )
        self.assertEqual(valid.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Enrollment.objects.filter(student=self.student, course=own_course).exists())

        invalid = self.client.post(
            "/api/v1/attendance/enrollments/",
            {"student": str(self.student.id), "course": str(other_course.id)},
            format="json",
        )
        self.assertEqual(invalid.status_code, status.HTTP_400_BAD_REQUEST)

    def test_lecturer_schedules_valid_class_session(self):
        course = Course.objects.create(code="CSC401", title="AI", lecturer=self.lecturer)
        self.authenticate(self.lecturer)
        response = self.client.post(
            "/api/v1/attendance/sessions/",
            {
                "course": str(course.id),
                "title": "Introduction to AI",
                "starts_at": "2026-07-21T09:00:00Z",
                "ends_at": "2026-07-21T11:00:00Z",
                "latitude": 51.5898,
                "longitude": -0.3346,
                "radius_metres": 100,
                "minimum_dwell_seconds": 30,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ClassSession.objects.get().course, course)

    def test_student_sees_only_enrolled_courses(self):
        visible = Course.objects.create(code="CSC401", title="AI", lecturer=self.lecturer)
        Course.objects.create(code="CSC402", title="Networks", lecturer=self.other_lecturer)
        Enrollment.objects.create(student=self.student, course=visible)
        self.authenticate(self.student)
        response = self.client.get("/api/v1/attendance/courses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["code"], "CSC401")


class GPSCheckInTests(APITestCase):
    def setUp(self):
        self.lecturer = User.objects.create_user(
            email="lecturer@example.com",
            password="StrongPass123!",
            full_name="Test Lecturer",
            role=User.Role.LECTURER,
            staff_number="LEC001",
        )
        self.student = User.objects.create_user(
            email="student@example.com",
            password="StrongPass123!",
            full_name="Test Student",
            role=User.Role.STUDENT,
            matric_number="STU001",
        )
        self.course = Course.objects.create(code="CSC401", title="AI", lecturer=self.lecturer)
        Enrollment.objects.create(student=self.student, course=self.course)
        self.session = ClassSession.objects.create(
            course=self.course,
            title="AI Lecture",
            starts_at=timezone.now() - timedelta(minutes=5),
            ends_at=timezone.now() + timedelta(minutes=55),
            latitude=51.5898,
            longitude=-0.3346,
            radius_metres=100,
            minimum_dwell_seconds=0,
        )
        self.client.force_authenticate(user=self.student)
        self.valid_reading = {
            "latitude": 51.5898,
            "longitude": -0.3346,
            "accuracy_metres": 10,
            "device_identifier": "device-test-001",
        }

    def test_haversine_same_point_is_zero(self):
        self.assertEqual(haversine_distance(51.5, -0.1, 51.5, -0.1), 0)

    def test_valid_two_step_check_in_is_confirmed(self):
        start = self.client.post(
            f"/api/v1/attendance/sessions/{self.session.id}/check-in/start/",
            self.valid_reading,
            format="json",
        )
        self.assertEqual(start.status_code, status.HTTP_201_CREATED)
        self.assertEqual(start.json()["status"], "pending_review")

        complete = self.client.post(
            f"/api/v1/attendance/attendance/{start.json()['id']}/check-in/complete/",
            self.valid_reading,
            format="json",
        )
        self.assertEqual(complete.status_code, status.HTTP_200_OK)
        self.assertEqual(complete.json()["status"], "confirmed")
        self.assertEqual(len(complete.json()["location_logs"]), 2)

    def test_outside_geofence_is_rejected(self):
        reading = self.valid_reading | {"latitude": 51.6000, "longitude": -0.3346}
        response = self.client.post(
            f"/api/v1/attendance/sessions/{self.session.id}/check-in/start/",
            reading,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()["status"], "rejected")

    def test_duplicate_attempt_is_blocked(self):
        first = self.client.post(
            f"/api/v1/attendance/sessions/{self.session.id}/check-in/start/",
            self.valid_reading,
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        duplicate = self.client.post(
            f"/api/v1/attendance/sessions/{self.session.id}/check-in/start/",
            self.valid_reading,
            format="json",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_409_CONFLICT)

    def test_unenrolled_student_is_blocked(self):
        Enrollment.objects.all().delete()
        response = self.client.post(
            f"/api/v1/attendance/sessions/{self.session.id}/check-in/start/",
            self.valid_reading,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_inactive_session_is_blocked(self):
        self.session.starts_at = timezone.now() + timedelta(hours=1)
        self.session.ends_at = timezone.now() + timedelta(hours=2)
        self.session.save()
        response = self.client.post(
            f"/api/v1/attendance/sessions/{self.session.id}/check-in/start/",
            self.valid_reading,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_device_change_remains_pending_for_review(self):
        start = self.client.post(
            f"/api/v1/attendance/sessions/{self.session.id}/check-in/start/",
            self.valid_reading,
            format="json",
        )
        changed = self.valid_reading | {"device_identifier": "different-device-002"}
        complete = self.client.post(
            f"/api/v1/attendance/attendance/{start.json()['id']}/check-in/complete/",
            changed,
            format="json",
        )
        self.assertEqual(complete.status_code, status.HTTP_200_OK)
        self.assertEqual(complete.json()["status"], "pending_review")
        self.assertGreater(AttendanceRecord.objects.get().risk_score, 0)
        self.assertTrue(FraudAlert.objects.filter(attendance_id=start.json()["id"]).exists())

    def create_flagged_attendance(self):
        start = self.client.post(
            f"/api/v1/attendance/sessions/{self.session.id}/check-in/start/",
            self.valid_reading,
            format="json",
        )
        changed = self.valid_reading | {"device_identifier": "different-device-002"}
        self.client.post(
            f"/api/v1/attendance/attendance/{start.json()['id']}/check-in/complete/",
            changed,
            format="json",
        )
        return FraudAlert.objects.get(attendance_id=start.json()["id"])

    def test_lecturer_can_review_flagged_attendance(self):
        alert = self.create_flagged_attendance()
        self.client.force_authenticate(user=self.lecturer)
        review = self.client.post(
            f"/api/v1/attendance/fraud-alerts/{alert.id}/review/",
            {"decision": "approved", "review_note": "Student identity and presence were verified."},
            format="json",
        )
        self.assertEqual(review.status_code, status.HTTP_200_OK)
        alert.refresh_from_db()
        alert.attendance.refresh_from_db()
        self.assertEqual(alert.review_status, FraudAlert.ReviewStatus.APPROVED)
        self.assertEqual(alert.attendance.status, AttendanceRecord.Status.CONFIRMED)

    def test_student_cannot_access_fraud_alerts(self):
        response = self.client.get("/api/v1/attendance/fraud-alerts/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_lecturer_dashboard_and_csv_report(self):
        self.client.force_authenticate(user=self.lecturer)
        dashboard = self.client.get("/api/v1/attendance/dashboard/summary/")
        self.assertEqual(dashboard.status_code, status.HTTP_200_OK)
        self.assertEqual(dashboard.json()["courses"], 1)

        report = self.client.get("/api/v1/attendance/reports/attendance.csv")
        self.assertEqual(report.status_code, status.HTTP_200_OK)
        self.assertEqual(report["Content-Type"], "text/csv")
        self.assertIn("attendance-report.csv", report["Content-Disposition"])
