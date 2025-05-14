import pandas as pd
import requests
from geopy.distance import geodesic
import os
import time

def filter_by_distance(points, min_distance_m=10):
    if not points:
        return []
    filtered = [points[0]]
    for pt in points[1:]:
        if geodesic(filtered[-1], pt).meters >= min_distance_m:
            filtered.append(pt)
    return filtered