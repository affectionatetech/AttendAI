from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "full_name",
            "email",
            "role",
            "matric_number",
            "staff_number",
            "is_active",
            "created_at",
        )
        read_only_fields = ("id", "is_active", "created_at")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "full_name", "email", "password", "role", "matric_number", "staff_number")
        read_only_fields = ("id",)

    def validate(self, attrs):
        role = attrs.get("role")
        if role == User.Role.ADMIN:
            raise serializers.ValidationError({"role": "Administrator accounts cannot be self-registered."})
        if role == User.Role.STUDENT and not attrs.get("matric_number"):
            raise serializers.ValidationError({"matric_number": "Students must provide a matric number."})
        if role == User.Role.LECTURER and not attrs.get("staff_number"):
            raise serializers.ValidationError({"staff_number": "Lecturers must provide a staff number."})
        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        if validated_data.get("matric_number"):
            validated_data["matric_number"] = validated_data["matric_number"].upper()
        if validated_data.get("staff_number"):
            validated_data["staff_number"] = validated_data["staff_number"].upper()
        return User.objects.create_user(password=password, **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(email=attrs["email"].lower(), password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Incorrect email or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account is disabled.")
        refresh = RefreshToken.for_user(user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        }

