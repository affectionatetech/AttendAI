from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LecturerListView, LoginView, ProfileView, RegisterView, StudentListView


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", ProfileView.as_view(), name="profile"),
    path("students/", StudentListView.as_view(), name="student-list"),
    path("lecturers/", LecturerListView.as_view(), name="lecturer-list"),
]
