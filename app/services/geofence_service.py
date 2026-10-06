"""
Geofence Service using the Haversine Formula.
Calculates the exact distance in meters between two GPS coordinates.
"""
from math import radians, cos, sin, asin, sqrt

def calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates distance in meters between two GPS points.
    """
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    
    r = 6371 # Radius of earth in kilometers
    return c * r * 1000 # Return distance in meters
