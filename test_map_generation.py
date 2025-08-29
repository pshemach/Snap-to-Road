#!/usr/bin/env python3
"""
Test script to verify dynamic map generation works correctly
"""

import pandas as pd
from app.visualize import create_route_map
import os

# Test data for different reps
test_data = {
    "rep_1": {
        "time_points": [
            [6.14264, 80.10011, pd.to_datetime("2024-01-15 10:30:00")],
            [6.43296, 80.00011, pd.to_datetime("2024-01-15 11:45:00")],
            [6.70941, 79.90764, pd.to_datetime("2024-01-15 12:30:00")]
        ],
        "snapped_path": [
            [6.14264, 80.10011],
            [6.43296, 80.00011],
            [6.70941, 79.90764]
        ],
        "route_coords": [
            [6.14264, 80.10011],
            [6.43296, 80.00011],
            [6.70941, 79.90764]
        ],
        "visits": [
            {
                "shop": "Hikkaduwa FC",
                "location": (6.14264, 80.10011),
                "check_in": pd.to_datetime("2024-01-15 10:30:00"),
                "check_out": pd.to_datetime("2024-01-15 10:35:00"),
                "duration_min": 5.0
            },
            {
                "shop": "Aluthgama FC",
                "location": (6.43296, 80.00011),
                "check_in": pd.to_datetime("2024-01-15 11:45:00"),
                "check_out": pd.to_datetime("2024-01-15 11:55:00"),
                "duration_min": 10.0
            }
        ]
    },
    "rep_2": {
        "time_points": [
            [6.20000, 80.20000, pd.to_datetime("2024-01-15 09:00:00")],
            [6.50000, 80.10000, pd.to_datetime("2024-01-15 10:00:00")]
        ],
        "snapped_path": [
            [6.20000, 80.20000],
            [6.50000, 80.10000]
        ],
        "route_coords": [
            [6.20000, 80.20000],
            [6.50000, 80.10000]
        ],
        "visits": [
            {
                "shop": "Test Shop",
                "location": (6.20000, 80.20000),
                "check_in": pd.to_datetime("2024-01-15 09:00:00"),
                "check_out": pd.to_datetime("2024-01-15 09:15:00"),
                "duration_min": 15.0
            }
        ]
    }
}

def test_map_generation():
    """Test map generation for different reps"""
    
    for rep_id, data in test_data.items():
        print(f"\nTesting map generation for {rep_id}...")
        
        # Generate map
        map_filename = f"test_map_{rep_id}.html"
        map_path = f"static/{map_filename}"
        
        try:
            create_route_map(
                time_points=data["time_points"],
                snapped_path=data["snapped_path"],
                visits=data["visits"],
                route_coords=data["route_coords"],
                output_path=map_path
            )
            
            # Check if file was created
            if os.path.exists(map_path):
                file_size = os.path.getsize(map_path)
                print(f"✓ Map generated successfully: {map_filename} ({file_size} bytes)")
                
                # Check if the file contains the correct data
                with open(map_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check for route coordinates
                if str(data["route_coords"][0][0]) in content:
                    print(f"✓ Route coordinates found in map")
                else:
                    print(f"✗ Route coordinates not found in map")
                
                # Check for visit data
                if data["visits"][0]["shop"] in content:
                    print(f"✓ Visit data found in map")
                else:
                    print(f"✗ Visit data not found in map")
                    
            else:
                print(f"✗ Map file was not created")
                
        except Exception as e:
            print(f"✗ Error generating map: {e}")
    
    # Clean up test files
    print("\nCleaning up test files...")
    for rep_id in test_data.keys():
        map_filename = f"test_map_{rep_id}.html"
        map_path = f"static/{map_filename}"
        if os.path.exists(map_path):
            os.remove(map_path)
            print(f"✓ Removed {map_filename}")

if __name__ == "__main__":
    test_map_generation()
