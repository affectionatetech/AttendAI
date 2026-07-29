# AttendAI Backend — Django Stage 4

This is the backend foundation for the AI-driven attendance management system described in the student's report.

## Implemented

- Django REST Framework project
- Student, lecturer, and administrator roles
- Student and lecturer registration
- Secure Django password hashing
- JWT login, token refresh, and protected profile
- Django administrator interface
- Database entities for courses, enrolments, sessions, attendance, location evidence, fraud alerts, and audit logs
- SQLite for easy development and PostgreSQL configuration for deployment
- Initial API tests
- Course creation and management
- Student enrolment and removal
- Class-session scheduling with coordinates, radius, and attendance window
- Role-based access for students, lecturers, and administrators
- Automatic audit entries for management actions
- Two-step GPS attendance check-in
- Haversine geofence distance calculation
- Attendance-window and enrolment checks
- Location-accuracy validation
- Server-timed dwell verification with a second GPS reading
- Duplicate-attempt prevention and device-consistency checks
- Role-filtered attendance history
- Explainable fraud-risk score and reason list
- Device-change, shared-coordinate, boundary, prior-alert, and impossible-travel indicators
- Isolation Forest contextual anomaly analysis after sufficient history exists
- Human-governed fraud-alert approval and rejection
- Lecturer/administrator dashboard summary
- Filterable CSV attendance export

## Windows setup

```powershell
cd attendance-system\backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python manage.py makemigrations accounts attendance
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/admin/` for the staff dashboard.

## Test

```powershell
python manage.py test tests
```

## Current API routes

- `GET /health/`
- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/token/refresh/`
- `GET /api/v1/auth/me/`
- `GET /api/v1/auth/students/`
- `GET, POST /api/v1/attendance/courses/`
- `GET, PATCH, DELETE /api/v1/attendance/courses/{id}/`
- `GET, POST /api/v1/attendance/enrollments/`
- `DELETE /api/v1/attendance/enrollments/{id}/`
- `GET, POST /api/v1/attendance/sessions/`
- `GET, PATCH, DELETE /api/v1/attendance/sessions/{id}/`
- `POST /api/v1/attendance/sessions/{id}/check-in/start/`
- `POST /api/v1/attendance/attendance/{id}/check-in/complete/`
- `GET /api/v1/attendance/attendance/history/`
- `GET /api/v1/attendance/fraud-alerts/`
- `POST /api/v1/attendance/fraud-alerts/{id}/review/`
- `GET /api/v1/attendance/dashboard/summary/`
- `GET /api/v1/attendance/reports/attendance.csv`

## Next stage

Professional lecturer/administrator web dashboard and student mobile application.

## Stage 5 web dashboard

The `web` folder contains the staff-facing React application with secure login,
dashboard statistics, courses, enrolments, class sessions, fraud review, and CSV reports.

Run the Django backend in the first terminal:

```powershell
cd backend
.venv\Scripts\Activate.ps1
python manage.py runserver
```

Open a second terminal and run the web application:

```powershell
cd web
npm install
npm run dev
```

Open `http://localhost:5173` and sign in with a lecturer or administrator account.

## Stage 6 student mobile application

The `mobile` folder contains the Expo student application. It includes student-only
login, enrolled courses, active sessions, precise GPS permission, two-reading dwell
verification, attendance outcomes, and history.

For an Android emulator, the default API address is `http://10.0.2.2:8000/api/v1`.

For a physical phone, find the laptop IPv4 address with `ipconfig`, add it to the
backend `.env` file, and create `mobile/.env` as shown below:

```env
EXPO_PUBLIC_API_URL=http://192.168.1.20:8000/api/v1
```

Replace `192.168.1.20` with the laptop's actual IPv4 address. The backend `.env`
must include the same address:

```env
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,10.0.2.2,192.168.1.20
```

Run Django so other devices on the local network can connect:

```powershell
python manage.py runserver 0.0.0.0:8000
```

Then, from the mobile folder:

```powershell
npm install
npx expo start
```

The laptop and phone must be connected to the same trusted Wi-Fi network.
