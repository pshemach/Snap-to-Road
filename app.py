# app.py
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
import os
import tempfile
from app.utils import filter_by_distance
from app.snap_to_road import snap_to_nearest_road_filtered
from app.get_direction import get_road_distance
from app.constant import ACCURACY_THRESHOLD, MIN_MOVE_DISTANCE_M, MAX_SNAP_DISTANCE_M
from app.visualize import detect_shop_visits, create_route_map

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('static', 'gps_ui_frontend.html')

@app.route('/upload-gps', methods=['POST'])
def upload_gps():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    filename = secure_filename(file.filename)
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        file.save(temp.name)
        df = pd.read_excel(temp.name) if filename.endswith('.xlsx') else pd.read_csv(temp.name)

    df.columns = df.columns.str.strip()
    if not {'Latitude', 'Longitude', 'Accuracy', 'DateTime'}.issubset(df.columns):
        return jsonify({"error": "Missing required columns in the file: Latitude, Longitude, Accuracy, DateTime"}), 400

    df = df[df['Accuracy'] <= ACCURACY_THRESHOLD]
    df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude', 'DateTime'])

    gps_points = list(zip(df['Latitude'], df['Longitude']))
    time_points = df[['Latitude', 'Longitude', 'DateTime']].values.tolist()

    filtered_points = filter_by_distance(gps_points, MIN_MOVE_DISTANCE_M)
    snapped_path = snap_to_nearest_road_filtered(filtered_points, MAX_SNAP_DISTANCE_M)
    total_distance, route_coords = get_road_distance(snapped_path)

    shops = [
        {"name": "Shop A", "location": (6.13852, 80.10066), "radius": 35},
        {"name": "Shop B", "location": (6.70941, 79.90764), "radius": 35},
    ]

    visits = detect_shop_visits(time_points, shops)
    map_path = create_route_map(time_points, snapped_path, visits, route_coords=route_coords)

    return jsonify({
        "total_distance_km": round(total_distance, 3),
        # "snapped_points_count": len(snapped_path),
        # "filtered_points_count": len(filtered_points),
        # "raw_points_count": len(gps_points),
        "shop_visits": visits,
        "map_url": "/static/route_map.html"
    })

if __name__ == '__main__':
    app.run(debug=True)