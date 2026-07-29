from rest_framework import generics, permissions, response, status, views

from .models import User
from .permissions import IsLecturerOrAdmin
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return response.Response(serializer.validated_data, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class StudentListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsLecturerOrAdmin]
    queryset = User.objects.filter(role=User.Role.STUDENT, is_active=True).order_by("full_name")


class LecturerListView(generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsLecturerOrAdmin]
    queryset = User.objects.filter(role=User.Role.LECTURER, is_active=True).order_by("full_name")
