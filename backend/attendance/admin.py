from django.contrib import admin

from .models import AttendanceRecord, AuditLog, ClassSession, Course, Enrollment, FraudAlert, LocationLog

admin.site.register([Course, Enrollment, ClassSession, AttendanceRecord, LocationLog, FraudAlert, AuditLog])

