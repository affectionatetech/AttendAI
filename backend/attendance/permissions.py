from rest_framework.permissions import BasePermission

from accounts.models import User


class CourseAccessPermission(BasePermission):
    """Students may read their courses; lecturers/admins may create and manage."""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return request.user.role in (User.Role.LECTURER, User.Role.ADMIN)

    def has_object_permission(self, request, view, obj):
        course = getattr(obj, "course", obj)
        if request.user.role == User.Role.ADMIN:
            return True
        if request.user.role == User.Role.LECTURER:
            return course.lecturer_id == request.user.id
        return request.method in ("GET", "HEAD", "OPTIONS") and course.students.filter(id=request.user.id).exists()


class LecturerOwnsCourseOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.LECTURER, User.Role.ADMIN)
        )
