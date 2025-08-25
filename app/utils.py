import pandas as pd
import requests
from geopy.distance import geodesic
import os
import time

def remove_concentrated_points(df, lat_col='Latitude', lon_col='Longitude', distance_threshold_m=40):
    """
    Removes spatially concentrated points from a DataFrame based on a minimum geodesic distance threshold.
    
    Parameters:
        df (pd.DataFrame): Input DataFrame containing GPS points.
        lat_col (str): Name of the latitude column.
        lon_col (str): Name of the longitude column.
        distance_threshold_m (float): Minimum distance in meters between retained points.
    
    Returns:
        pd.DataFrame: Filtered DataFrame with spaced-out points.
    """
    cleaned_rows = []
    last_point = None

    for _, row in df.iterrows():
        current_point = (row[lat_col], row[lon_col])
        if last_point is None:
            cleaned_rows.append(row)
            last_point = current_point
        else:
            distance = geodesic(last_point, current_point).meters
            if distance >= distance_threshold_m:
                cleaned_rows.append(row)
                last_point = current_point

    return pd.DataFrame(cleaned_rows)

def filter_by_distance(points, min_distance_m=10):
    if not points:
        return []
    filtered = [points[0]]
    for pt in points[1:]:
        if geodesic(filtered[-1], pt).meters >= min_distance_m:
            filtered.append(pt)
    return filtered