# Snap-to-Road Rep Route Analysis

A Flask application for analyzing GPS routes of sales representatives, with road snapping and shop visit detection.

## New Features (Updated)

### Batch Processing Workflow with Dynamic Map Generation

The application now supports a more efficient workflow with dynamic map generation:

1. **Process All Reps**: Click the "Process All Reps" button to calculate distances and routes for all representatives at once. This saves only the raw data (snapped points, visits, coordinates) without creating maps.

2. **Select and View**: After processing, select a rep from the dropdown to:

   - Instantly load their analysis data from saved storage
   - Dynamically generate a map using the saved data
   - Display the route visualization with animations

3. **Persistent Storage**: Processed data is automatically saved to `processed_rep_data.json` and persists between server restarts.

4. **Dynamic Map Generation**: Maps are generated on-demand when a rep is selected, using the saved snapped points and route data.

### Key Benefits

- **Faster Processing**: No map generation during batch processing - only saves essential data
- **Dynamic Maps**: Maps are generated fresh each time a rep is selected
- **Data Persistence**: Processed data survives server restarts
- **Memory Efficient**: Only stores raw data, not large map files
- **Clear Data Option**: Clear processed data and generated maps to reprocess if needed

### Usage

1. Start the application: `python app.py`
2. Open the web interface
3. Click "Process All Reps" to calculate data for all representatives (saves raw data only)
4. Select any rep from the dropdown to view their analysis and generate their map
5. Use "Clear Processed Data" if you need to reprocess

### API Endpoints

- `POST /process-all-reps` - Process all reps and save raw data
- `GET /get-processed-rep-data/<rep_id>` - Get saved data for a specific rep
- `GET /generate-map/<rep_id>` - Generate map dynamically from saved data
- `GET /get-processing-status` - Check if data has been processed
- `POST /clear-processed-data` - Clear all saved data and generated maps

### File Structure

- `app.py` - Main Flask application
- `static/gps_ui_frontend.html` - Web interface
- `processed_rep_data.json` - Persistent storage for raw processed data
- `static/route_map_*.html` - Dynamically generated map files (created on-demand)
- `data/Gps-Collection.csv` - GPS data source

### Data Flow

1. **Processing Phase**:

   - Load GPS data → Filter → Snap to roads → Calculate distances → Detect visits
   - Save only raw data (coordinates, visits, distances) to JSON

2. **Viewing Phase**:
   - Load saved raw data for selected rep
   - Convert data back to proper format
   - Generate map dynamically using saved coordinates
   - Display route with animations

## Original Features

- GPS route visualization with road snapping
- Shop visit detection and duration calculation
- Interactive map with route animation
- Distance calculation using road networks
- Accuracy filtering and point concentration removal
