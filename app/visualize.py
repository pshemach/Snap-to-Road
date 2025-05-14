# app/visualize.py
import os
import folium
from folium.plugins import TimestampedGeoJson
from geopy.distance import geodesic
from jinja2 import Template
from datetime import timedelta

def merge_close_visits(visits, gap_threshold_min=5):
    if not visits:
        return []
    merged = [visits[0]]
    for visit in visits[1:]:
        last = merged[-1]
        # Same shop and within time threshold
        if (visit['shop'] == last['shop'] and
            (visit['check_in'] - last['check_out']).total_seconds() / 60 <= gap_threshold_min):
            # Extend current visit
            last['check_out'] = visit['check_out']
            last['duration_min'] = round((last['check_out'] - last['check_in']).total_seconds() / 60, 2)
        else:
            merged.append(visit)
    return merged

def detect_shop_visits(time_points, shops, min_duration_min=1):
    visits = []
    for shop in shops:
        in_zone, check_in = False, None
        for i, (lat, lon, ts) in enumerate(time_points):
            if geodesic((lat, lon), shop['location']).meters <= shop['radius']:
                if not in_zone:
                    in_zone = True
                    check_in = ts
            else:
                if in_zone:
                    out_time = time_points[i - 1][2]
                    duration = (out_time - check_in).total_seconds() / 60
                    if duration >= min_duration_min:
                        visits.append({
                            "shop": shop['name'], "location": shop['location'],
                            "check_in": check_in, "check_out": out_time,
                            "duration_min": round(duration, 2)
                        })
                    in_zone = False
    return merge_close_visits(visits)

def create_route_map(time_points, snapped_path, visits, route_coords=None, output_path='static/route_map.html'):
    m = folium.Map(location=snapped_path[0], zoom_start=16)

    if route_coords:
        folium.PolyLine(route_coords, color="blue", weight=4, opacity=0.6).add_to(m)

    for visit in visits:
        folium.CircleMarker(
            location=visit['location'], radius=8, color='orange', fill=True,
            fill_opacity=0.7,
            popup=f"{visit['shop']}\nDuration: {visit['duration_min']} min"
        ).add_to(m)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    m.save(output_path)

    animation_js = """
<style>
#infoBox, #controls {
    position: absolute;
    z-index: 1000;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    font-size: 16px;
    padding: 10px 15px;
}
#infoBox {
    top: 20px;
    right: 20px;
    border: 1px solid #ccc;
}
#controls {
    bottom: 20px;
    left: 20px;
    border: 1px solid #999;
    width: 300px;
}
#progressBar {
    width: 100%%;
    margin-top: 10px;
}
</style>
<div id='infoBox'>Status: <span id='statusText'>Loading...</span></div>
<div id='controls'>
  <button onclick="play()">▶️ Play</button>
  <button onclick="pause()">⏸ Pause</button>
  <label>Speed: <input type="range" min="0.5" max="3" value="1" step="0.1" id="speedSlider"></label>
  <input id="progressBar" type="range" min="0" max="%d" value="0">
</div>
<script>
const route = %s;
const visits = %s;
let i = 0;
let marker = null;
let playing = true;
let speed = 1;
const statusBox = document.getElementById('statusText');
document.getElementById('speedSlider').oninput = e => speed = parseFloat(e.target.value);
const progressBar = document.getElementById('progressBar');
progressBar.oninput = e => { i = parseInt(e.target.value); updateCar(map); };
function play() { playing = true; moveCar(map); }
function pause() { playing = false; }

function isWaitingHere(lat, lng) {
  for (const v of visits) {
    const dist = Math.sqrt((v.lat - lat)**2 + (v.lng - lng)**2);
    if (dist < 0.0005) return v;
  }
  return null;
}

function updateCar(map) {
  const [lat, lng] = route[i];
  const stop = isWaitingHere(lat, lng);
  const status = stop ? `Waiting at ${stop.shop}: ${stop.duration_min} min` : 'Moving...';
  statusBox.innerText = status;
  if (!marker) {
    marker = L.marker([lat, lng], {
      icon: L.icon({
        iconUrl: 'https://cdn-icons-png.flaticon.com/512/870/870130.png',
        iconSize: [32, 32],
        iconAnchor: [16, 16]
      })
    }).addTo(map);
  } else {
    marker.setLatLng([lat, lng]);
  }
  if (stop) marker.bindPopup(status).openPopup();
  else marker.closePopup();
  progressBar.value = i;
}

function moveCar(map) {
  if (i >= route.length || !playing) return;
  updateCar(map);
  const [lat, lng] = route[i];
  const stop = isWaitingHere(lat, lng);
  const stepTime = 60000 / route.length; // 1 min for whole journey
  const pauseMs = stop ? stop.duration_min * 1000 : stepTime / speed;
  i++;
  setTimeout(() => moveCar(map), pauseMs);
}

window.onload = function() {
  map = Object.values(window).find(v => v instanceof L.Map);
  setTimeout(() => moveCar(map), 1000);
};
</script>
"""

    timed_route = [[lat, lon] for lat, lon in route_coords]
    visit_points = [
        {
            'shop': v['shop'],
            'lat': v['location'][0],
            'lng': v['location'][1],
            'duration_min': v['duration_min']
        }
        for v in visits
    ]

    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(animation_js % (len(timed_route) - 1, timed_route, visit_points))

    return output_path