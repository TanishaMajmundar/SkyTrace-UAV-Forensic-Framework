def find_altitude_column(rows):
    if not rows:
        return None

    possible_names = [
        "OSD.altitude",
        "Altitude",
        "ALT",
        "GPS:Height",
        "Height",
        "IMU_ATTI(0):relativeHeight:C"
    ]

    for key in rows[0].keys():
        if key in possible_names:
            return key

    return None

def get_recent_altitudes(rows, time_col, alt_col, window_seconds=10):
    data = []

    for r in rows:
        try:
            t = float(r[time_col])
            alt = float(r[alt_col])
            data.append((t, alt))
        except:
            continue

    if not data:
        return []

    data.sort(key=lambda x: x[0])
    end_time = data[-1][0]

    return [alt for t, alt in data if end_time - t <= window_seconds]

def classify_termination(rows, time_col, alt_col):

    if not alt_col:
        return {
            "status": "UNKNOWN",
            "reason": "Altitude data not available"
        }

    recent_alts = get_recent_altitudes(rows, time_col, alt_col)

    if not recent_alts:
        return {
            "status": "UNKNOWN",
            "reason": "Insufficient altitude data"
        }

    end_altitude = recent_alts[-1]
    max_recent_alt = max(recent_alts)
    min_recent_alt = min(recent_alts)

    descent = max_recent_alt - min_recent_alt

    # thresholds (can be tuned later)
    GROUND_ALT = 2.0        # meters
    RAPID_DESCENT = 5.0     # meters

    if end_altitude <= GROUND_ALT:
        return {
            "status": "NORMAL LANDING",
            "reason": "Flight ended near ground level"
        }

    if descent >= RAPID_DESCENT:
        return {
            "status": "POSSIBLE CRASH",
            "reason": "Rapid descent detected before log termination"
        }

    return {
        "status": "ABRUPT TERMINATION",
        "reason": "Log ended while airborne without landing phase"
    }
