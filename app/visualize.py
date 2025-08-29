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
        if (visit['shop'] == last['shop'] and
            (visit['check_in'] - last['check_out']).total_seconds() / 60 <= gap_threshold_min):
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
    # Calculate center from snapped path
    if snapped_path:
        center_lat = sum(point[0] for point in snapped_path) / len(snapped_path)
        center_lon = sum(point[1] for point in snapped_path) / len(snapped_path)
        center = [center_lat, center_lon]
    else:
        center = [6.139873800984828, 80.09971544832543]  # Default center
    
    m = folium.Map(location=center, zoom_start=10)

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

    # Generate dynamic JavaScript with actual data
    timed_route = [[lat, lon] for lat, lon in route_coords] if route_coords else []
    visit_points = [
        {
            'shop': v['shop'],
            'lat': v['location'][0],
            'lng': v['location'][1],
            'duration_min': v['duration_min'],
            'check_in': v['check_in'].strftime('%H:%M'),
            'check_out': v['check_out'].strftime('%H:%M')
        } for v in visits
    ]

    animation_js = f"""
<div id='controls' style="position:absolute; bottom:20px; left:20px; background:white; padding:10px; border-radius:8px; box-shadow:0 2px 8px rgba(0,0,0,0.2); z-index:1000">
  <button onclick="play()">▶️ Play</button>
  <button onclick="pause()">⏸ Pause</button>
  <label>Speed: <input type="range" min="0.5" max="3" value="1" step="0.1" id="speedSlider"></label>
  <input id="progressBar" type="range" min="0" max="{len(timed_route)-1}" value="0" style="width:100%;">
</div>
<script>
const route = {timed_route};
const visits = {visit_points};
let i = 0;
let marker = null;
let playing = true;
let speed = 1;
const progressBar = document.getElementById('progressBar');
document.getElementById('speedSlider').oninput = e => speed = parseFloat(e.target.value);
progressBar.oninput = e => {{ i = parseInt(e.target.value); updateCar(map); }};
function play() {{ playing = true; moveCar(map); }}
function pause() {{ playing = false; }}
function isWaitingHere(lat, lng) {{
  for (let j = 0; j < visits.length; j++) {{
    const v = visits[j];
    const dist = Math.sqrt((v.lat - lat)**2 + (v.lng - lng)**2);
    if (dist < 0.0005) return {{ stop: v, index: j }};
  }}
  return null;
}}
function updateCar(map) {{
  const [lat, lng] = route[i];
  const res = isWaitingHere(lat, lng);
  const stop = res ? res.stop : null;
  const index = res ? res.index : null;
  const status = stop ? `Waiting at ${{stop.shop}}: ${{stop.duration_min}} min` : 'Moving...';
  parent.postMessage({{ statusText: status, highlightIndex: index }}, '*');
  if (!marker) {{
    marker = L.marker([lat, lng], {{
      icon: L.icon({{
        iconUrl: 'https://cdn-icons-png.flaticon.com/512/870/870130.png',
        iconSize: [32, 32], iconAnchor: [16, 16]
      }})
    }}).addTo(map);
  }} else {{
    marker.setLatLng([lat, lng]);
  }}
  if (stop) marker.bindPopup(status).openPopup();
  else marker.closePopup();
  progressBar.value = i;
}}
function moveCar(map) {{
  if (i >= route.length || !playing) return;
  updateCar(map);
  const [lat, lng] = route[i];
  const res = isWaitingHere(lat, lng);
  const stop = res ? res.stop : null;
  const stepTime = 60000 / route.length;
  const pauseMs = stop ? stop.duration_min * 1000 : stepTime / speed;
  i++;
  setTimeout(() => moveCar(map), pauseMs);
}}
window.onload = function() {{
  map = Object.values(window).find(v => v instanceof L.Map);
  setTimeout(() => moveCar(map), 1000);
}};
</script>
"""

    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(animation_js)

    return output_path