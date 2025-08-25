import requests
from geopy.distance import geodesic
import os
import time
import polyline
from dotenv import load_dotenv

# Load .env file
load_dotenv()

API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

def get_road_distance(points, max_direct_distance_m=50):
    total_km = 0
    route_coords = []

    for i in range(len(points) - 1):
        origin = points[i]
        destination = points[i + 1]
        distance_m = geodesic(origin, destination).meters

        if distance_m <= max_direct_distance_m:
            total_km += distance_m / 1000
            if not route_coords or route_coords[-1] != origin:
                route_coords.append(origin)
            route_coords.append(destination)
        else:
            # Use Google Directions API for road-based path
            url = (
                f"https://maps.googleapis.com/maps/api/directions/json?"
                f"origin={origin[0]},{origin[1]}&destination={destination[0]},{destination[1]}"
                f"&key={API_KEY}"
            )

            r = requests.get(url).json()
            if r.get("status") == "OK":
                try:
                    poly = r["routes"][0]["overview_polyline"]["points"]
                    route_coords.extend(polyline.decode(poly))
                    for leg in r["routes"][0]["legs"]:
                        total_km += leg["distance"]["value"] / 1000
                except Exception as e:
                    print(f"Polyline decode error at segment {i}: {e}")
            else:
                print(f"Directions error [{i}]:", r.get("status"), r.get("error_message"))
                # fallback to geodesic
                total_km += distance_m / 1000
                route_coords.append(origin)
                route_coords.append(destination)

            time.sleep(0.1)  # API rate limit safety

    return total_km, route_coords