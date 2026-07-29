from math import asin, cos, radians, sin, sqrt


EARTH_RADIUS_METRES = 6_371_000
MAX_ACCEPTABLE_ACCURACY_METRES = 100


def haversine_distance(latitude_1, longitude_1, latitude_2, longitude_2):
    """Return the great-circle distance between two GPS coordinates in metres."""
    lat_1, lon_1, lat_2, lon_2 = map(
        radians, (latitude_1, longitude_1, latitude_2, longitude_2)
    )
    delta_latitude = lat_2 - lat_1
    delta_longitude = lon_2 - lon_1
    value = (
        sin(delta_latitude / 2) ** 2
        + cos(lat_1) * cos(lat_2) * sin(delta_longitude / 2) ** 2
    )
    return 2 * EARTH_RADIUS_METRES * asin(sqrt(value))


def validate_location(class_session, latitude, longitude, accuracy_metres):
    distance = haversine_distance(
        latitude,
        longitude,
        class_session.latitude,
        class_session.longitude,
    )
    accurate = accuracy_metres <= MAX_ACCEPTABLE_ACCURACY_METRES
    within_geofence = distance <= class_session.radius_metres
    return {
        "distance_metres": round(distance, 2),
        "is_accurate": accurate,
        "is_within_geofence": within_geofence,
        "is_valid": accurate and within_geofence,
    }

