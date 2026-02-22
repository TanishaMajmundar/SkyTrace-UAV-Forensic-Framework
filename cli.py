import sys
import os
import subprocess
import matplotlib.pyplot as plt
from Analysis import timeline
from Analysis import battery
from Analysis.timeline import (
    load_csv,
    find_time_column,
    build_timeline,
    detect_abrupt_end,
    seconds_to_hhmmss,
    hhmmss_to_seconds,
    get_gps_start_time
)
from Analysis.termination import classify_termination
from Analysis.altitude_motion import altitude_motion_analysis
from Analysis.battery import battery_anomaly_analysis
from Analysis.plot import extract_gps_points, plot_flight_path
from Analysis.battery import  plot_battery_step_terminal
from Analysis.altitude_motion import plot_altitude_profile_terminal


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATCON_PATH = os.path.join("Tools", "datcon", "DatCon.4.3.0.exe")

def check_datcon_or_exit():
    if os.path.exists(DATCON_PATH):
        return  

    print("\n❌ DatCon not found.")
    print("\nThis tool requires DatCon to convert DJI DAT files.")
    print("\n➡ Download DatCon from:")
    print("   https://datfile.net/DatCon/")
    print("\nAfter downloading:")
    print("1. Extract DatCon.4.3.0.exe")
    print("2. Place it inside:")
    print("   Tools/datcon/")
    print("3. Re-run this tool\n")

    input("Press Enter after installing DatCon to retry, or Ctrl+C to exit...")


def convert_dat_to_csv(dat_path):
    # Check DatCon first
    check_datcon_or_exit()

    if not os.path.exists(dat_path):
        print("❌ DAT file not found:", dat_path)
        sys.exit(1)

    print("🔄 Converting DAT to CSV using DatCon...")

    try:
        subprocess.run(
            [DATCON_PATH, dat_path],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("❌ DatCon failed to convert the DAT file")
        print(e)
        sys.exit(1)

    csv_path = dat_path.replace(".DAT", ".csv")

    if not os.path.exists(csv_path):
        print("❌ CSV file was not generated")
        sys.exit(1)

    print("✅ Conversion successful:", csv_path)
    return csv_path


def show_termination(termination):
    print("\n🛑 Flight Termination Analysis")
    print("Termination type:", termination["status"])
    print("Reason:", termination["reason"])


def show_battery(battery):
    print("\n🔋 Battery Analysis")
    print("Battery status:", battery["status"])
    print("Reason:", battery["reason"])
    print("Battery at start:", battery["start_cap"], "%")
    print("Battery at end:", battery["end_cap"], "%")
    print("Voltage at start:", round(battery["start_volt"], 2), "V")
    print("Voltage at end:", round(battery["end_volt"], 2), "V")
    print("\nSMART Battery Thresholds")
    print("Go-Home threshold:", battery["go_home_threshold"], "%")
    print("Land threshold:", battery["land_threshold"], "%")
    print("\nSMART Battery Usage")
    print("Go-Home condition used:", "YES" if battery["go_home_used"] else "NO")
    print("Land condition used:", "YES" if battery["land_used"] else "NO")


def show_timeline(timeline, rows, time_col, gps_lat_col):
    print("\n📊 Flight Timeline")
    print("Start time:", seconds_to_hhmmss(timeline["start_time"]), "UTC")
    print("End time:", seconds_to_hhmmss(timeline["end_time"]), "UTC")
    print("Duration:", timeline["duration"], "seconds")
    print("Duration (HH:MM:SS):", seconds_to_hhmmss(timeline["duration"]))
    print("Records:", timeline["total_records"])
    abrupt = detect_abrupt_end(rows, time_col)
    print("Abrupt termination detected:", abrupt)
    gps_start = get_gps_start_time(rows, time_col, gps_lat_col)

    if gps_start is not None:
        flight_start = timeline["start_time"]
        delay = gps_start - flight_start
        print("\n📍 GPS Availability")
        print("GPS data available from:", seconds_to_hhmmss(gps_start))
        print("GPS acquisition delay:", delay, "seconds")
    else:
        print("\n📍 GPS Availability")
        print("No GPS data found in log")


def show_altitude_motion(alt_motion):
    print("\n🏔️ Altitude & Motion Analysis")
    print("Maximum altitude:", alt_motion["max_altitude"], "m")
    print("End altitude:", alt_motion["end_altitude"], "m")
    if alt_motion["end_altitude"] < 0:
        print(
            "Note: Negative end altitude indicates landing below takeoff reference "
            "(relative height), not a crash."
        )
    print("Rapid descent detected:", alt_motion["rapid_descent"])
    print("Descent rate near end:", alt_motion["descent_rate"], "m/s")
    if alt_motion["descent_rate"] < 0:
        print(
            "Note: Negative descent rate indicates downward motion. "
        )
    if alt_motion["end_altitude"] <= 1.0 and not alt_motion["rapid_descent"]:
        print("Conclusion: Controlled landing detected")
    elif alt_motion["rapid_descent"]:
        print("Conclusion: Abnormal descent detected (possible crash)")


def show_gps(lats, lons):
    if lats and lons:
        print("\n📍 GPS Coordinates Summary")
        print("Start location (takeoff):")
        print("  Latitude :", round(lats[0], 6))
        print("  Longitude:", round(lons[0], 6))
        print("\nEnd location (last known):")
        print("  Latitude :", round(lats[-1], 6))
        print("  Longitude:", round(lons[-1], 6))
    else:
        print("\n📍 GPS Coordinates Summary")
        print("No valid GPS coordinates available")
    choice = input("\nPlot flight path? (y/n): ").lower()
    if choice == "y":
        plot_flight_path(lats, lons)
        
        
def show_final_summary(timeline,termination,battery,lats,lons,alt_motion):    
    print("\n" + "=" * 50)
    print("🧾 FINAL FORENSIC SUMMARY")
    print("=" * 50)
    # Timeline
    print(f"Flight duration        : {timeline['duration']} seconds ({seconds_to_hhmmss(timeline['duration'])})")
    print(f"Flight records         : {timeline['total_records']}")
    # Termination
    print(f"Termination type       : {termination['status']}")
    print(f"Termination reason     : {termination['reason']}")
    # Battery
    print(f"Battery status         : {battery['status']}")
    print(f"Battery end percentage : {battery['end_cap']} %")
    # SMART battery
    print(f"Go-Home used           : {'YES' if battery['go_home_used'] else 'NO'}")
    print(f"Forced landing used    : {'YES' if battery['land_used'] else 'NO'}")
    # GPS
    if lats and lons:
        print("Last known GPS location:")
        print(f"  Latitude             : {round(lats[-1], 6)}")
        print(f"  Longitude            : {round(lons[-1], 6)}")
    else:
        print("Last known GPS location: Not available")
    # Altitude summary
    print("\nAltitude Summary:")
    print(f"Maximum altitude       : {round(alt_motion['max_altitude'], 2)} m")
    print(f"End altitude           : {round(alt_motion['end_altitude'], 2)} m")
    if alt_motion["end_altitude"] < 0:
        print(
            "Note: Negative end altitude indicates landing below takeoff reference "
        )
    if alt_motion["end_altitude"] <= 1.0 and not alt_motion["rapid_descent"]:
        print("Altitude interpretation: Controlled descent to ground level")
    elif alt_motion["rapid_descent"]:
        print("Altitude interpretation: Abnormal rapid descent detected")
    else:
        print("Altitude interpretation: Inconclusive")

    # Final conclusion
    print("\n🔎 Final Conclusion:")
    if termination["status"] == "NORMAL LANDING":
        print("The flight concluded with a controlled landing and no evidence of crash or power failure.")
    elif termination["status"] == "POSSIBLE CRASH":
        print("The flight shows signs consistent with an abnormal termination or possible crash.")
    else:
        print("The flight termination could not be conclusively classified.")


def main():

    while True:
        print("\nAnalyze CSV file")
        print("1. For csv file analysis")
        print("2. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            csv_path = input("Enter path to CSV file: ").strip().strip('"')
            if not os.path.exists(csv_path):
                print("❌ CSV file not found")
                continue   # Go back to menu
            break          # Valid input → exit loop and continue program

        elif choice == "2":
            print("Exiting Tool")
            return

        else:
            print("❌ Invalid choice. Please try again.")


    rows = load_csv(csv_path)
    time_col = find_time_column(rows)
    gps_lat_col = "GPS:Lat"   
    termination = classify_termination(rows, time_col)
    battery = battery_anomaly_analysis(rows, time_col)
    lats, lons = extract_gps_points(rows)
    if not time_col:
        print("No time column found")
        return
    timeline = build_timeline(rows, time_col)
    alt_motion = altitude_motion_analysis(
        rows,
        time_col,
        "IMU_ATTI(0):relativeHeight:C"
    )
    
    while True:
        print("\n" + "-" * 40)
        print("Drone Forensics Tool")
        print("1. Show Flight Timeline")
        print("2. Show Termination Analysis")
        print("3. Show Battery Analysis")
        print("4. Show GPS Summary")
        print("5. Plot Flight Path")
        print("6. Show Altitude & Motion Analysis")
        print("7. Show Final Forensic Summary")
        print("0. Exit")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            show_timeline(timeline, rows, time_col, gps_lat_col)
                    
        elif choice == "2":
            show_termination(termination)

        elif choice == "3":
            show_battery(battery)
            plot_battery_step_terminal(rows, time_col)

        elif choice == "4":
            show_gps(lats, lons)

        elif choice == "5":
            plot_flight_path(lats, lons)

        elif choice == "6":
            show_altitude_motion(alt_motion)
            plot_altitude_profile_terminal(
                rows,
                time_col,
                "IMU_ATTI(0):relativeHeight:C"
            )
            
        elif choice == "7":
            show_final_summary(
                timeline, termination, battery, lats, lons, alt_motion
            )

        elif choice == "0":
            print("Exiting tool.")
            break

        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()