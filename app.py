# app.py
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import pandas as pd
import os
import tempfile
import json
from app.utils import filter_by_distance, remove_concentrated_points
from app.snap_to_road import snap_to_nearest_road_filtered
from app.get_direction import get_road_distance
from app.constant import ACCURACY_THRESHOLD, MIN_MOVE_DISTANCE_M, MAX_SNAP_DISTANCE_M
from app.visualize import detect_shop_visits, create_route_map

app = Flask(__name__)

# Global storage for processed rep data
processed_rep_data = {}

# File path for persistent storage
PROCESSED_DATA_FILE = 'processed_rep_data.json'

def load_processed_data():
    """Load processed data from JSON file"""
    global processed_rep_data
    if os.path.exists(PROCESSED_DATA_FILE):
        try:
            with open(PROCESSED_DATA_FILE, 'r') as f:
                data = json.load(f)
                
                # Validate and clean the loaded data
                for rep_id, rep_data in data.items():
                    # Ensure all required fields exist
                    if isinstance(rep_data, dict):
                        validated_data = {
                            "total_distance_km": rep_data.get("total_distance_km", 0),
                            "shop_visits": rep_data.get("shop_visits", []),
                            "route_coords": rep_data.get("route_coords", []),
                            "snapped_path": rep_data.get("snapped_path", []),
                            "time_points": rep_data.get("time_points", [])
                        }
                        processed_rep_data[rep_id] = validated_data
                    else:
                        print(f"Warning: Invalid data format for rep {rep_id}")
                        
            print(f"Loaded {len(processed_rep_data)} processed rep records")
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in processed data file: {e}")
            # Remove corrupted file
            try:
                os.remove(PROCESSED_DATA_FILE)
                print("Removed corrupted processed data file")
            except:
                pass
        except Exception as e:
            print(f"Error loading processed data: {e}")

def save_processed_data():
    """Save processed data to JSON file"""
    try:
        # Test JSON serialization before saving
        json.dumps(processed_rep_data, indent=2)
        
        with open(PROCESSED_DATA_FILE, 'w') as f:
            json.dump(processed_rep_data, f, indent=2)
        print(f"Saved {len(processed_rep_data)} processed rep records")
    except TypeError as e:
        print(f"Error: Data contains non-serializable objects: {e}")
        # Try to save only the essential data
        essential_data = {}
        for rep_id, rep_data in processed_rep_data.items():
            essential_data[rep_id] = {
                "total_distance_km": rep_data.get("total_distance_km", 0),
                "shop_visits": rep_data.get("shop_visits", []),
                "route_coords": rep_data.get("route_coords", []),
                "snapped_path": rep_data.get("snapped_path", []),
                "time_points": rep_data.get("time_points", [])
            }
        try:
            with open(PROCESSED_DATA_FILE, 'w') as f:
                json.dump(essential_data, f, indent=2)
            print(f"Saved essential data for {len(essential_data)} reps")
        except Exception as e2:
            print(f"Failed to save even essential data: {e2}")
    except Exception as e:
        print(f"Error saving processed data: {e}")

# Load CSV once for all sessions
GPS_CSV_PATH = 'data/Gps-Collection.csv'
if os.path.exists(GPS_CSV_PATH):
    full_df = pd.read_csv(GPS_CSV_PATH)
    full_df = full_df.dropna()
    full_df.columns = full_df.columns.str.strip()
else:
    full_df = pd.DataFrame()

# Load previously processed data on startup
load_processed_data()

def process_single_rep(rep_id):
    """Process a single rep and return the results"""
    df = full_df.copy()
    df = df[df['RepId'].astype(str) == rep_id]
    df = df[df['Accuracy'] <= ACCURACY_THRESHOLD]
    df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude', 'DateTime'])

    if df.empty:
        return None

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
    
    # Convert visits to JSON-serializable format
    serializable_visits = []
    for visit in visits:
        serializable_visit = {
            "shop": visit["shop"],
            "location": list(visit["location"]),  # Convert tuple to list
            "check_in": visit["check_in"].isoformat() if hasattr(visit["check_in"], 'isoformat') else str(visit["check_in"]),
            "check_out": visit["check_out"].isoformat() if hasattr(visit["check_out"], 'isoformat') else str(visit["check_out"]),
            "duration_min": visit["duration_min"]
        }
        serializable_visits.append(serializable_visit)

    # Convert route_coords to JSON-serializable format
    serializable_route_coords = []
    if route_coords:
        for coord in route_coords:
            if isinstance(coord, (list, tuple)):
                serializable_route_coords.append([float(x) for x in coord])
            else:
                serializable_route_coords.append(float(coord))

    # Convert snapped_path to JSON-serializable format
    serializable_snapped_path = []
    if snapped_path:
        for point in snapped_path:
            if isinstance(point, (list, tuple)):
                serializable_snapped_path.append([float(x) for x in point])
            else:
                serializable_snapped_path.append(float(point))

    # Convert time_points to JSON-serializable format
    serializable_time_points = []
    for point in time_points:
        lat, lon, dt = point
        serializable_time_points.append([
            float(lat),
            float(lon),
            dt.isoformat() if hasattr(dt, 'isoformat') else str(dt)
        ])

    return {
        "total_distance_km": round(total_distance, 3),
        "shop_visits": serializable_visits,
        "route_coords": serializable_route_coords,
        "snapped_path": serializable_snapped_path,
        "time_points": serializable_time_points
    }

def generate_map_from_saved_data(rep_id):
    """Generate map from saved data for a specific rep"""
    if rep_id not in processed_rep_data:
        return None
    
    rep_data = processed_rep_data[rep_id]
    
    # Convert saved data back to the format expected by create_route_map
    time_points = []
    for point in rep_data["time_points"]:
        lat, lon, dt_str = point
        dt = pd.to_datetime(dt_str)
        time_points.append([lat, lon, dt])
    
    snapped_path = rep_data["snapped_path"]
    route_coords = rep_data["route_coords"]
    
    # Convert visits back to the format expected by create_route_map
    visits = []
    for visit_data in rep_data["shop_visits"]:
        visit = {
            "shop": visit_data["shop"],
            "location": tuple(visit_data["location"]),  # Convert list back to tuple
            "check_in": pd.to_datetime(visit_data["check_in"]),
            "check_out": pd.to_datetime(visit_data["check_out"]),
            "duration_min": visit_data["duration_min"]
        }
        visits.append(visit)
    
    # Generate unique map file for this rep
    map_filename = f"route_map_{rep_id}.html"
    map_path = f"static/{map_filename}"
    
    # Create the map with the actual data for this rep
    create_route_map(time_points, snapped_path, visits, route_coords=route_coords, output_path=map_path)
    
    return f"/static/{map_filename}"

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

@app.route('/process-all-reps', methods=['POST'])
def process_all_reps():
    """Process all reps and store the results"""
    global processed_rep_data
    
    if 'RepId' not in full_df.columns:
        return jsonify({"error": "No RepId column found in data"}), 400
    
    rep_ids = full_df['RepId'].astype(str).unique()
    processed_count = 0
    errors = []
    
    for rep_id in rep_ids:
        try:
            result = process_single_rep(rep_id)
            if result:
                processed_rep_data[rep_id] = result
                processed_count += 1
            else:
                errors.append(f"No valid data for Rep ID: {rep_id}")
        except Exception as e:
            errors.append(f"Error processing Rep ID {rep_id}: {str(e)}")
    
    # Save processed data to file
    save_processed_data()
    
    return jsonify({
        "message": f"Processed {processed_count} reps successfully",
        "processed_count": processed_count,
        "total_reps": len(rep_ids),
        "errors": errors
    })

@app.route('/get-processed-rep-data/<rep_id>')
def get_processed_rep_data(rep_id):
    """Get processed data for a specific rep"""
    if rep_id in processed_rep_data:
        return jsonify(processed_rep_data[rep_id])
    else:
        return jsonify({"error": "No processed data found for this rep"}), 404

@app.route('/generate-map/<rep_id>')
def generate_map(rep_id):
    """Generate map for a specific rep from saved data"""
    if rep_id not in processed_rep_data:
        return jsonify({"error": "No processed data found for this rep"}), 404
    
    try:
        map_url = generate_map_from_saved_data(rep_id)
        if map_url:
            return jsonify({"map_url": map_url})
        else:
            return jsonify({"error": "Failed to generate map"}), 500
    except Exception as e:
        return jsonify({"error": f"Error generating map: {str(e)}"}), 500

@app.route('/get-processing-status')
def get_processing_status():
    """Get the current processing status"""
    if 'RepId' not in full_df.columns:
        return jsonify({"total_reps": 0, "processed_count": 0})
    
    total_reps = len(full_df['RepId'].astype(str).unique())
    processed_count = len(processed_rep_data)
    
    return jsonify({
        "total_reps": total_reps,
        "processed_count": processed_count,
        "is_processed": processed_count > 0
    })

@app.route('/clear-processed-data', methods=['POST'])
def clear_processed_data():
    """Clear all processed data"""
    global processed_rep_data
    processed_rep_data = {}
    
    # Remove the file if it exists
    if os.path.exists(PROCESSED_DATA_FILE):
        os.remove(PROCESSED_DATA_FILE)
    
    # Clean up generated map files
    import glob
    map_files = glob.glob('static/route_map_*.html')
    for map_file in map_files:
        try:
            os.remove(map_file)
            print(f"Removed map file: {map_file}")
        except Exception as e:
            print(f"Error removing map file {map_file}: {e}")
    
    return jsonify({"message": "All processed data and generated maps cleared successfully"})

@app.route('/process-rep', methods=['POST'])
def process_rep():
    data = request.get_json()
    rep_id = str(data.get('rep_id')).strip()

    print(type(rep_id))

    if not rep_id:
        return jsonify({"error": "Missing rep_id in request"}), 400

    result = process_single_rep(rep_id)
    if result is None:
        return jsonify({"error": "No valid data found for selected Rep ID"}), 400

    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7097, debug=True)