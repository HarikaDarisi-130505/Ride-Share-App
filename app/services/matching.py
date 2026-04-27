
import polyline
import math
import json
from typing import List, Tuple

def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371e3  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def is_point_near_polyline(point: Tuple[float, float], polyline_str: str, threshold_meters: float = 300) -> bool:
    """
    Check if a point (lat, lon) is within threshold_meters of any point on the polyline.
    """
    if not polyline_str:
        return False
        
    try:
        if polyline_str.startswith("["):
            path = json.loads(polyline_str)
            coords = [(p['latitude'], p['longitude']) for p in path]
        else:
            coords = polyline.decode(polyline_str)
            
        for lat, lon in coords:
            dist = haversine_distance(point[0], point[1], lat, lon)
            if dist <= threshold_meters:
                return True
        return False
    except Exception as e:
        print(f"Matching Error: {e}")
        return False

def smart_match(origin: Tuple[float, float], destination: Tuple[float, float], polyline_str: str, threshold: float = 1500) -> bool:
    """
    Check if both origin and destination are near the polyline in the correct order.
    """
    if not polyline_str:
        return False
        
    try:
        if polyline_str.startswith("["):
            path = json.loads(polyline_str)
            coords = [(p['latitude'], p['longitude']) for p in path]
        else:
            coords = polyline.decode(polyline_str)
            
        origin_idx = -1
        dest_idx = -1
        
        # Find first point near origin
        for i, (lat, lon) in enumerate(coords):
            if haversine_distance(origin[0], origin[1], lat, lon) <= threshold:
                origin_idx = i
                break
        
        if origin_idx == -1:
            return False
            
        # Find point near destination AFTER origin_idx
        for i in range(origin_idx + 1, len(coords)):
            lat, lon = coords[i]
            if haversine_distance(destination[0], destination[1], lat, lon) <= threshold:
                dest_idx = i
                break
                
        return dest_idx > origin_idx
    except Exception as e:
        print(f"Smart Match Error: {e}")
        return False
