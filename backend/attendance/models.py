import uuid

from django.conf import settings
from django.db import models


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=150)
    lecturer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="courses_taught")
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, through="Enrollment", related_name="enrolled_courses")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.title}"


class Enrollment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("student", "course"), name="unique_student_course")]


class ClassSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="sessions")
    title = models.CharField(max_length=150)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    radius_metres = models.PositiveIntegerField(default=100)
    minimum_dwell_seconds = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        CONFIRMED = "confirmed", "Confirmed"
        REJECTED = "rejected", "Rejected"
        PENDING_REVIEW = "pending_review", "Pending review"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    session = models.ForeignKey(ClassSession, on_delete=models.CASCADE, related_name="attendance_records")
    status = models.CharField(max_length=20, choices=Status.choices)
    checked_in_at = models.DateTimeField(auto_now_add=True)
    risk_score = models.FloatField(default=0)
    decision_reason = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("student", "session"), name="unique_student_session_attendance")
        ]


class LocationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attendance = models.ForeignKey(AttendanceRecord, on_delete=models.CASCADE, related_name="location_logs")
    latitude = models.FloatField()
    longitude = models.FloatField()
    accuracy_metres = models.FloatField()
    distance_metres = models.FloatField()
    is_within_geofence = models.BooleanField()
    device_identifier = models.CharField(max_length=128, blank=True)
    reading_type = models.CharField(max_length=20, default="initial")
    captured_at = models.DateTimeField(auto_now_add=True)



class FraudAlert(models.Model):
    class ReviewStatus(models.TextChoices):
        OPEN = "open", "Open"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    attendance = models.OneToOneField(AttendanceRecord, on_delete=models.CASCADE, related_name="fraud_alert")
    risk_score = models.FloatField()
    reasons = models.JSONField(default=list)
    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.OPEN)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50)
    entity_id = models.UUIDField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
