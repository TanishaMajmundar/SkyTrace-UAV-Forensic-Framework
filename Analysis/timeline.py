import csv

def hhmmss_to_seconds(hhmmss):
    """
    Converts HHMMSS (e.g., 183952) to seconds since midnight
    """
    hhmmss = int(hhmmss)

    seconds = hhmmss % 100
    minutes = (hhmmss // 100) % 100
    hours = hhmmss // 10000

    return hours * 3600 + minutes * 60 + seconds

def seconds_to_hhmmss(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

def load_csv(csv_path):
    with open(csv_path, newline="", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows

def find_time_column(rows):
    if not rows:
        return None

    possible_names = [
        "time", "Time", "timestamp", "Timestamp",
        "TimeMS", "OSD.time", "GPS:Time"
    ]

    for key in rows[0].keys():
        if key in possible_names:
            return key

    return None


def build_timeline(rows, time_col):
    times = []

    for r in rows:
        try:
            t = hhmmss_to_seconds(r[time_col])
            times.append(t)
        except:
            continue

    if not times:
        return None

    start = min(times)
    end = max(times)
    duration = end - start

    return {
        "start_time": start,
        "end_time": end,
        "duration": duration,
        "total_records": len(times)
    }

def detect_abrupt_end(rows, time_col, gap_threshold=5.0):
    times = []

    for r in rows:
        try:
            times.append(float(r[time_col]))
        except:
            continue

    times.sort()

    if len(times) < 2:
        return False

    last_gap = times[-1] - times[-2]

    return last_gap > gap_threshold

def get_gps_start_time(rows, time_col, gps_lat_col):
    """
    Returns the earliest time (in seconds) where GPS data is available
    """
    gps_times = []

    for r in rows:
        try:
            lat = r.get(gps_lat_col, "").strip()
            if lat and lat != "0":
                t = hhmmss_to_seconds(r[time_col])
                gps_times.append(t)
        except:
            continue

    if not gps_times:
        return None

    return min(gps_times)


import plotext as plt
from collections import defaultdict
from Analysis.timeline import hhmmss_to_seconds

def plot_record_density_terminal(rows, time_col, interval=30):
    buckets = defaultdict(int)

    for r in rows:
        try:
            t = hhmmss_to_seconds(r[time_col])
        except:
            continue

        bucket = (t // interval) * interval
        buckets[bucket] += 1

    if not buckets:
        print("❌ No timeline data")
        return

    times = sorted(buckets.keys())
    counts = [buckets[t] for t in times]

    t0 = times[0]
    times_min = [(t - t0) / 60 for t in times]

    plt.clear_data()
    plt.title("Flight Timeline (Log Record Density)")
    plt.xlabel("Time since start (minutes)")
    plt.ylabel("Records per interval")
    plt.bar(times_min, counts)
    plt.show()
