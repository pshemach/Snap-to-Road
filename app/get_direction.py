import requests
from geopy.distance import geodesic
import os
import time
import polyline

API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'YOUR_GOOGLE_MAPS_API_KEY')

def get_road_distance(points):
    total_km = 0
    route_coords = []
    for i in range(0, len(points) - 1, 24):
        segment = points[i:i+25]
        origin = segment[0]
        destination = segment[-1]
        waypoints = "|".join([f"via:{lat},{lng}" for lat, lng in segment[1:-1]])
        url = (
            f"https://maps.googleapis.com/maps/api/directions/json?"
            f"origin={origin[0]},{origin[1]}&destination={destination[0]},{destination[1]}"
            f"&waypoints={waypoints}&key={API_KEY}"
        )
        r = requests.get(url).json()
        if r["status"] == "OK":
            for leg in r["routes"][0]["legs"]:
                total_km += leg["distance"]["value"] / 1000  # meters to km
            poly = r["routes"][0]["overview_polyline"]["points"]
            route_coords.extend(polyline.decode(poly))
        else:
            print("Directions error:", r.get("status"), r.get("error_message"))
        time.sleep(0.1)
    return total_km, route_coords