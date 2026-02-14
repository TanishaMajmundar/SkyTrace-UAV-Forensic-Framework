import matplotlib.pyplot as plt

def extract_gps_points(rows):
    lat_col = "GPS:Lat"
    lon_col = "GPS:Long"

    lats = []
    lons = []

    for r in rows:
        try:
            lat = float(r[lat_col])
            lon = float(r[lon_col])

            if lat == 0.0 or lon == 0.0:
                continue

            lats.append(lat)
            lons.append(lon)
        except:
            continue

    return lats, lons


def plot_flight_path(lats, lons):
    if len(lats) < 2:
        print("Not enough GPS data to plot path")
        return

    plt.figure()
    plt.plot(lons, lats)
    plt.scatter(lons[0], lats[0])      # start
    plt.scatter(lons[-1], lats[-1])    # end

    plt.title("Drone Flight Path")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    plt.grid(True)
    plt.axis("equal")
    plt.show()
