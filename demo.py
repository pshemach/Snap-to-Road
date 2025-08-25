# app.py
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
import os
import tempfile
from app.utils import filter_by_distance, remove_concentrated_points
from app.snap_to_road import snap_to_nearest_road_filtered
from app.get_direction import get_road_distance
from app.constant import ACCURACY_THRESHOLD, MIN_MOVE_DISTANCE_M, MAX_SNAP_DISTANCE_M
from app.visualize import detect_shop_visits, create_route_map

app = Flask(__name__)

# Load CSV once for all sessions
GPS_CSV_PATH = 'data/Gps-Collection.csv'
if os.path.exists(GPS_CSV_PATH):
    full_df = pd.read_csv(GPS_CSV_PATH)
    full_df = full_df.dropna()
    full_df.columns = full_df.columns.str.strip()
else:
    full_df = pd.DataFrame()

@app.route('/')
def index():
    return send_from_directory('static', 'gps_ui_frontend.html')

@app.route('/rep-ids')
def get_rep_ids():
    if 'RepId' not in full_df.columns or 'RepName' not in full_df.columns:
        return jsonify({"rep_ids": []})
    
    rep_df = full_df[['RepId', 'RepName']].drop_duplicates()
    rep_list = [
        {"id": str(row.RepId), "name": row.RepName}
        for _, row in rep_df.iterrows()
    ]
    return jsonify({"rep_ids": rep_list})

@app.route('/process-rep', methods=['POST'])
def process_rep():
    data = request.get_json()
    rep_id = str(data.get('rep_id')).strip()

    print(type(rep_id))

    if not rep_id:
        return jsonify({"error": "Missing rep_id in request"}), 400

    df = full_df.copy()
    df = df[df['RepId'].astype(str) == rep_id]
    df = df[df['Accuracy'] <= ACCURACY_THRESHOLD]
    df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude', 'DateTime'])

    if df.empty:
        return jsonify({"error": "No valid data found for selected Rep ID"}), 400

    gps_points = list(zip(df['Latitude'], df['Longitude']))
    time_points = df[['Latitude', 'Longitude', 'DateTime']].values.tolist()

    filtered_points = filter_by_distance(gps_points, MIN_MOVE_DISTANCE_M)
    snapped_path = snap_to_nearest_road_filtered(filtered_points, MAX_SNAP_DISTANCE_M)
    total_distance, route_coords = get_road_distance(snapped_path)

    shops = [
        {"name": "Hikkaduwa FC", "location": (6.14264, 80.10011), "radius": 35},
        {"name": "Aluthgama FC", "location": (6.43296, 80.00011), "radius": 35},
        {"name": "Panadura FC", "location": (6.70941, 79.90764), "radius": 35},
    ]

    visits = detect_shop_visits(time_points, shops)
    map_path = create_route_map(time_points, snapped_path, visits, route_coords=route_coords)

    return jsonify({
        "total_distance_km": round(total_distance, 3),
        "shop_visits": visits,
        "map_url": "/static/route_map.html"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7097)