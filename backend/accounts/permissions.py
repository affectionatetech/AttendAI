from rest_framework.permissions import BasePermission

from .models import User


class IsLecturerOrAdmin(BasePermission):
    message = "Only lecturers and administrators can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role in (User.Role.LECTURER, User.Role.ADMIN)
        )


class IsAdministrator(BasePermission):
    message = "Only administrators can perform this action."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.ADMIN
        )

