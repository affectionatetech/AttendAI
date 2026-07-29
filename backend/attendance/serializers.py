from django.utils import timezone
from rest_framework import serializers

from accounts.models import User
from accounts.serializers import UserSerializer
from .models import AttendanceRecord, AuditLog, ClassSession, Course, Enrollment, FraudAlert, LocationLog


class CourseSerializer(serializers.ModelSerializer):
    lecturer_name = serializers.CharField(source="lecturer.full_name", read_only=True)
    student_count = serializers.IntegerField(source="students.count", read_only=True)

    class Meta:
        model = Course
        fields = ("id", "code", "title", "lecturer", "lecturer_name", "student_count", "created_at")
        read_only_fields = ("id", "created_at", "lecturer_name", "student_count")
        extra_kwargs = {"lecturer": {"required": False}}

    def validate_lecturer(self, lecturer):
        if lecturer.role != User.Role.LECTURER:
            raise serializers.ValidationError("The selected user is not a lecturer.")
        return lecturer

    def validate(self, attrs):
        request = self.context["request"]
        if request.user.role == User.Role.LECTURER:
            attrs["lecturer"] = request.user
        elif not attrs.get("lecturer") and not self.instance:
            raise serializers.ValidationError({"lecturer": "An administrator must select a lecturer."})
        return attrs


class EnrollmentSerializer(serializers.ModelSerializer):
    student_details = UserSerializer(source="student", read_only=True)
    course_code = serializers.CharField(source="course.code", read_only=True)

    class Meta:
        model = Enrollment
        fields = ("id", "student", "student_details", "course", "course_code", "enrolled_at")
        read_only_fields = ("id", "student_details", "course_code", "enrolled_at")

    def validate_student(self, student):
        if student.role != User.Role.STUDENT:
            raise serializers.ValidationError("Only a student can be enrolled in a course.")
        return student

    def validate(self, attrs):
        request = self.context["request"]
        course = attrs.get("course")
        if request.user.role == User.Role.LECTURER and course.lecturer_id != request.user.id:
            raise serializers.ValidationError({"course": "You can only enrol students in your own course."})
        if Enrollment.objects.filter(student=attrs.get("student"), course=course).exists():
            raise serializers.ValidationError("This student is already enrolled in the course.")
        return attrs


class ClassSessionSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
    is_active = serializers.SerializerMethodField()

    class Meta:
        model = ClassSession
        fields = (
            "id",
            "course",
            "course_code",
            "title",
            "starts_at",
            "ends_at",
            "latitude",
            "longitude",
            "radius_metres",
            "minimum_dwell_seconds",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "course_code", "is_active", "created_at")

    def get_is_active(self, obj):
        now = timezone.now()
        return obj.starts_at <= now <= obj.ends_at

    def validate(self, attrs):
        request = self.context["request"]
        course = attrs.get("course") or self.instance.course
        starts_at = attrs.get("starts_at", getattr(self.instance, "starts_at", None))
        ends_at = attrs.get("ends_at", getattr(self.instance, "ends_at", None))
        if ends_at <= starts_at:
            raise serializers.ValidationError({"ends_at": "The end time must be after the start time."})
        if request.user.role == User.Role.LECTURER and course.lecturer_id != request.user.id:
            raise serializers.ValidationError({"course": "You can only schedule sessions for your own course."})
        return attrs


def write_audit_log(user, action, instance):
    AuditLog.objects.create(
        actor=user,
        action=action,
        entity_type=instance.__class__.__name__,
        entity_id=instance.id,
    )


class LocationReadingSerializer(serializers.Serializer):
    latitude = serializers.FloatField(min_value=-90, max_value=90)
    longitude = serializers.FloatField(min_value=-180, max_value=180)
    accuracy_metres = serializers.FloatField(min_value=0, max_value=5000)
    device_identifier = serializers.CharField(min_length=8, max_length=128)


class LocationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationLog
        fields = (
            "latitude",
            "longitude",
            "accuracy_metres",
            "distance_metres",
            "is_within_geofence",
            "reading_type",
            "captured_at",
        )


class AttendanceRecordSerializer(serializers.ModelSerializer):
    session_title = serializers.CharField(source="session.title", read_only=True)
    course_code = serializers.CharField(source="session.course.code", read_only=True)
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    location_logs = LocationLogSerializer(many=True, read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = (
            "id",
            "student",
            "student_name",
            "session",
            "session_title",
            "course_code",
            "status",
            "checked_in_at",
            "risk_score",
            "decision_reason",
            "location_logs",
        )
        read_only_fields = fields


class FraudAlertSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="attendance.student.full_name", read_only=True)
    matric_number = serializers.CharField(source="attendance.student.matric_number", read_only=True)
    course_code = serializers.CharField(source="attendance.session.course.code", read_only=True)
    session_title = serializers.CharField(source="attendance.session.title", read_only=True)
    reviewed_by_name = serializers.CharField(source="reviewed_by.full_name", read_only=True)

    class Meta:
        model = FraudAlert
        fields = (
            "id",
            "attendance",
            "student_name",
            "matric_number",
            "course_code",
            "session_title",
            "risk_score",
            "reasons",
            "review_status",
            "reviewed_by",
            "reviewed_by_name",
            "reviewed_at",
            "review_note",
            "created_at",
        )
        read_only_fields = fields


class FraudReviewSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=("approved", "rejected"))
    review_note = serializers.CharField(min_length=3, max_length=1000)
