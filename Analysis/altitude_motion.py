def extract_altitude_series(rows, time_col, alt_col):
    data = []

    for r in rows:
        try:
            t = int(r[time_col])
            alt = float(r[alt_col])
            data.append((t, alt))
        except:
            continue

    data.sort(key=lambda x: x[0])
    return data

def altitude_statistics(data):
    if not data:
        return None

    altitudes = [alt for _, alt in data]

    return {
        "max_altitude": max(altitudes),
        "min_altitude": min(altitudes),
        "end_altitude": altitudes[-1]
    }

def detect_rapid_descent(data, window=5):
    if len(data) < 2:
        return False, 0.0

    end_time = data[-1][0]
    recent = [(t, alt) for t, alt in data if end_time - t <= window]

    if len(recent) < 2:
        return False, 0.0

    start_alt = recent[0][1]
    end_alt = recent[-1][1]

    descent = start_alt - end_alt
    rate = descent / window  # m/s

    RAPID_DESCENT_RATE = 2.5  # m/s (reasonable UAV threshold)

    return rate > RAPID_DESCENT_RATE, rate

def altitude_motion_analysis(rows, time_col):
    ALT_COL = "IMU_ATTI(0):relativeHeight:C"

    data = extract_altitude_series(rows, time_col, ALT_COL)

    if not data:
        return {
            "status": "UNKNOWN",
            "reason": "Altitude data not available"
        }

    stats = altitude_statistics(data)
    rapid, rate = detect_rapid_descent(data)

    result = {
        "max_altitude": round(stats["max_altitude"], 2),
        "end_altitude": round(stats["end_altitude"], 2),
        "rapid_descent": rapid,
        "descent_rate": round(rate, 2)
    }

    return result


import plotext as plt
from Analysis.timeline import hhmmss_to_seconds

def plot_altitude_profile_terminal(rows, time_col, alt_col):
    times, alts = [], []

    for r in rows:
        try:
            t = hhmmss_to_seconds(r[time_col])
            alt = float(r[alt_col])
        except:
            continue

        times.append(t)
        alts.append(alt)

    if not times:
        print("❌ No altitude data")
        return

    t0 = times[0]
    times_min = [(t - t0) / 60 for t in times]

    plt.clear_data()
    plt.plotsize(100, 25)
    plt.title("Altitude Profile")
    plt.xlabel("Time since takeoff (minutes)")
    plt.ylabel("Altitude (m)")
    plt.plot(times_min, alts)
    plt.show()

    print("\n🔍 Altitude Summary")
    print(f"Maximum Altitude : {round(max(alts), 2)} m")
    print(f"End Altitude     : {round(alts[-1], 2)} m")

    if alts[-1] <= 1.0:
        print("Conclusion       : Controlled landing detected")
