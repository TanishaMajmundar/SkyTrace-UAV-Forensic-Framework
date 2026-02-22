def extract_battery_series(rows, time_col, cap_col, volt_col, gohome_col, land_col):
    data = []

    for r in rows:
        try:
            t = int(r[time_col])
            cap = float(r[cap_col])
            volt = float(r[volt_col]) / 1000.0  # mV → V

            go_home = float(r[gohome_col]) if gohome_col in r and r[gohome_col] != "" else None
            land = float(r[land_col]) if land_col in r and r[land_col] != "" else None

            data.append((t, cap, volt, go_home, land))
        except:
            continue

    data.sort(key=lambda x: x[0])
    return data


def battery_statistics(data):
    if not data:
        return None

    caps = [cap for _, cap, _, _, _ in data]
    volts = [v for _, _, v, _, _ in data]

    gohomes = [gh for _, _, _, gh, _ in data if gh is not None]
    lands = [l for _, _, _, _, l in data if l is not None]

    return {
        "start_cap": caps[0],
        "end_cap": caps[-1],
        "min_cap": min(caps),

        "start_volt": volts[0],
        "end_volt": volts[-1],
        "min_volt": min(volts),

        "go_home": gohomes[-1] if gohomes else None,
        "land": lands[-1] if lands else None
    }


def interpret_smart_battery(stats):
    end_cap = stats["end_cap"]
    go_home = stats["go_home"]
    land = stats["land"]

    if land is not None and end_cap <= land:
        return "Forced landing due to low battery (SMART_BATT land threshold reached)"

    if go_home is not None and end_cap <= go_home:
        return "Return-to-home condition reached before landing"

    return "SMART battery thresholds not violated"


def smart_battery_usage(stats):
    end_cap = stats["end_cap"]
    go_home = stats["go_home"]
    land = stats["land"]

    usage = {
        "go_home_threshold": go_home,
        "land_threshold": land,
        "go_home_used": False,
        "land_used": False
    }

    if go_home is not None and end_cap <= go_home:
        usage["go_home_used"] = True

    if land is not None and end_cap <= land:
        usage["land_used"] = True

    return usage


def detect_battery_anomaly(data):
    stats = battery_statistics(data)

    if not stats:
        return {
            "status": "UNKNOWN",
            "reason": "Battery data unavailable"
        }

    LOW_BATTERY_PCT = 20
    CRITICAL_VOLT_DROP = 1.5  # volts

    volt_drop = stats["start_volt"] - stats["end_volt"]

    if stats["end_cap"] <= LOW_BATTERY_PCT:
        return {
            "status": "LOW BATTERY",
            "reason": "Flight ended with low battery level"
        }

    if volt_drop >= CRITICAL_VOLT_DROP and stats["end_cap"] > LOW_BATTERY_PCT:
        return {
            "status": "POSSIBLE POWER FAILURE",
            "reason": "Sudden voltage drop with sufficient battery capacity"
        }

    return {
        "status": "BATTERY HEALTHY",
        "reason": "Battery level and voltage within normal range"
    }


def battery_anomaly_analysis(rows, time_col, cap_col, volt_col, gohome_col, land_col):

    if not cap_col or not volt_col:
        return {
            "status": "UNAVAILABLE",
            "reason": "Battery columns not mapped"
        }

    data = extract_battery_series(
        rows,
        time_col,
        cap_col,
        volt_col,
        gohome_col,
        land_col
    )

    if not data:
        return {
            "status": "UNKNOWN",
            "reason": "Battery data not found"
        }

    stats = battery_statistics(data)
    anomaly = detect_battery_anomaly(data)
    smart_interp = interpret_smart_battery(stats)
    usage = smart_battery_usage(stats)

    result = {
        "status": anomaly["status"],
        "reason": anomaly["reason"],

        "start_cap": stats["start_cap"],
        "end_cap": stats["end_cap"],
        "start_volt": stats["start_volt"],
        "end_volt": stats["end_volt"],

        "go_home_threshold": usage["go_home_threshold"],
        "land_threshold": usage["land_threshold"],
        "go_home_used": usage["go_home_used"],
        "land_used": usage["land_used"]
    }


    return result


import plotext as plt
from collections import defaultdict
from Analysis.timeline import hhmmss_to_seconds

def plot_battery_step_terminal(rows, time_col, cap_col):
    minute_bucket = defaultdict(list)
    raw_caps = []
    for r in rows:
        try:
            t_sec = hhmmss_to_seconds(r[time_col])
            cap = float(r[cap_col])
            raw_caps.append(cap)
        except:
            continue

        minute = t_sec // 60          # bucket per minute
        minute_bucket[minute].append(cap)

    if not minute_bucket:
        print("❌ No battery data available")
        return

    # sort minutes
    minutes = sorted(minute_bucket.keys())

    # take average battery per minute (can also take last value)
    battery_per_min = [
        sum(minute_bucket[m]) / len(minute_bucket[m])
        for m in minutes
    ]

    # normalize time to start from 0
    start_min = minutes[0]
    x_vals = [m - start_min for m in minutes]

    # ── TERMINAL STEP BAR GRAPH ─────────────
    plt.clear_data()
    plt.plotsize(100, 30)

    plt.title("Battery Percentage vs Time (per minute)")
    plt.xlabel("Time (minutes)")
    plt.ylabel("Battery %")

    # Y-axis from 0 to 100
    plt.ylim(0, 100)

    # 🔑 10% gap on Y-axis
    plt.yticks(list(range(0, 101, 10)))

    # Solid per-minute blocks (no gaps)
    plt.bar(
        x_vals,
        battery_per_min,
        width=1.0
    )

    # X-axis ticks at each minute
    plt.xticks(x_vals[::2])
    plt.grid()


    plt.show()

    # ── DETAILS BELOW GRAPH ─────────────────
    print("\n🔍 Battery Step Summary")

    start_cap = raw_caps[0]
    end_cap = raw_caps[-1]

    print(f"Start Battery : {round(start_cap, 2)} %")
    print(f"End Battery   : {round(end_cap, 2)} %")
    print(f"Total Minutes : {len(battery_per_min)}")

    drop = start_cap - end_cap
    print(f"Total Drop    : {round(drop, 2)} %")

    if end_cap <= 20:
        print("⚠️  Battery reached critical level")
    else:
        print("✅ Battery stayed above critical level")
