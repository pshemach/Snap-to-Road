import requests
from geopy.distance import geodesic
import os
import time

API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', 'YOUR_GOOGLE_MAPS_API_KEY')

# Snap to Roads (max 100 per batch)
def snap_to_nearest_road_filtered(points, max_snap_distance_m=15):
    snapped = []
    for i in range(0, len(points), 100):
        batch = points[i:i+100]
        path = "|".join([f"{lat},{lng}" for lat, lng in batch])
        url = f"https://roads.googleapis.com/v1/snapToRoads?path={path}&interpolate=false&key={API_KEY}"
        r = requests.get(url)
        data = r.json()

        if 'snappedPoints' in data:
            for p in data['snappedPoints']:
                if 'originalIndex' not in p:
                    continue
                idx = p['originalIndex']
                original = batch[idx]
                snapped_point = (p['location']['latitude'], p['location']['longitude'])

                distance = geodesic(original, snapped_point).meters
                if distance <= max_snap_distance_m:
                    snapped.append(snapped_point)
        else:
            print("Snap error:", data.get("status"), data.get("error_message"))
        time.sleep(0.1)
    return snapped