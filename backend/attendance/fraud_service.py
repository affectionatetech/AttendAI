from datetime import timedelta

from django.db.models import Count
from sklearn.ensemble import IsolationForest

from .models import AttendanceRecord, FraudAlert, LocationLog
from .services import haversine_distance


REVIEW_THRESHOLD = 0.50
MINIMUM_AI_HISTORY = 20


def _feature_vector(attendance, final_log, device_changed):
    return [
        min(final_log.distance_metres / max(attendance.session.radius_metres, 1), 5),
        min(final_log.accuracy_metres / 100, 5),
        1 if device_changed else 0,
    ]


def _historical_vectors():
    records = (
        AttendanceRecord.objects.select_related("session")
        .prefetch_related("location_logs")
        .exclude(status=AttendanceRecord.Status.REJECTED)
    )
    vectors = []
    for record in records:
        logs = list(record.location_logs.order_by("captured_at"))
        if len(logs) < 2:
            continue
        vectors.append(_feature_vector(record, logs[-1], logs[0].device_identifier != logs[-1].device_identifier))
    return vectors


def calculate_fraud_risk(attendance, initial_log, final_log):
    """Return an explainable risk score and reasons without making a punitive decision."""
    score = 0.0
    reasons = []
    device_changed = initial_log.device_identifier != final_log.device_identifier

    if device_changed:
        score += 0.55
        reasons.append("The device identifier changed during the same check-in.")

    edge_ratio = final_log.distance_metres / max(attendance.session.radius_metres, 1)
    if edge_ratio >= 0.85:
        score += 0.20
        reasons.append("The final reading was repeatedly close to the geofence boundary.")

    matching_coordinates = (
        LocationLog.objects.filter(
            attendance__session=attendance.session,
            latitude=final_log.latitude,
            longitude=final_log.longitude,
        )
        .exclude(attendance__student=attendance.student)
        .values("attendance__student")
        .distinct()
        .count()
    )
    if matching_coordinates:
        score += 0.45
        reasons.append("The exact coordinates were also submitted by another student in this session.")

    prior_alerts = FraudAlert.objects.filter(attendance__student=attendance.student).count()
    if prior_alerts:
        contribution = min(prior_alerts * 0.05, 0.15)
        score += contribution
        reasons.append(f"The account has {prior_alerts} previous flagged attendance event(s).")

    previous_log = (
        LocationLog.objects.filter(
            attendance__student=attendance.student,
            attendance__status=AttendanceRecord.Status.CONFIRMED,
            captured_at__lt=initial_log.captured_at,
        )
        .exclude(attendance=attendance)
        .order_by("-captured_at")
        .first()
    )
    if previous_log:
        elapsed_hours = (initial_log.captured_at - previous_log.captured_at).total_seconds() / 3600
        if 0 < elapsed_hours <= 6:
            travelled_km = haversine_distance(
                previous_log.latitude,
                previous_log.longitude,
                initial_log.latitude,
                initial_log.longitude,
            ) / 1000
            speed = travelled_km / elapsed_hours
            if speed > 300:
                score += 0.50
                reasons.append("The location change from the previous confirmed event appears implausibly fast.")

    history = _historical_vectors()
    ai_used = len(history) >= MINIMUM_AI_HISTORY
    if ai_used:
        model = IsolationForest(contamination="auto", random_state=42)
        model.fit(history)
        current = [_feature_vector(attendance, final_log, device_changed)]
        if model.predict(current)[0] == -1:
            score += 0.25
            reasons.append("The contextual AI model identified this event as unusual compared with attendance history.")

    score = round(min(score, 1.0), 2)
    return {
        "risk_score": score,
        "reasons": reasons,
        "requires_review": score >= REVIEW_THRESHOLD,
        "ai_model_used": ai_used,
        "history_count": len(history),
    }


def create_alert(attendance, assessment):
    return FraudAlert.objects.create(
        attendance=attendance,
        risk_score=assessment["risk_score"],
        reasons=assessment["reasons"],
    )

