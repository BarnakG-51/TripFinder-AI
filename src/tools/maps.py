"""
Maps tool for calculating distances and travel times between locations.
This tool simulates map/distance calculation functionality.
"""

from typing import Dict, Any, List
import math


def calculate_distance(origin: str, destination: str) -> Dict[str, Any]:
    """
    Calculate distance between two locations.
    
    Args:
        origin: Starting location
        destination: Destination location
    
    Returns:
        Dictionary with distance and travel time information
    """
    # Simulated distance calculation (would use Google Maps API in production)
    # Using a simple hash-based approach for consistent "distances"
    hash_val = abs(hash(f"{origin}-{destination}")) % 1000
    distance_km = 100 + hash_val
    
    result = {
        "origin": origin,
        "destination": destination,
        "distance_km": distance_km,
        "distance_miles": round(distance_km * 0.621371, 2),
        "driving_time": f"{distance_km // 60}h {distance_km % 60}m",
        "flying_time": f"{distance_km // 500}h {(distance_km % 500) // 10}m"
    }
    
    print(f"[MAPS] Distance from {origin} to {destination}: {distance_km} km")
    return result


def get_route(origin: str, destination: str, waypoints: List[str] = None) -> Dict[str, Any]:
    """
    Get route information including waypoints.
    
    Args:
        origin: Starting location
        destination: Final destination
        waypoints: List of intermediate stops (optional)
    
    Returns:
        Dictionary with route information
    """
    waypoints = waypoints or []
    total_distance = 0
    segments = []
    
    # Calculate distance for each segment
    current = origin
    for next_point in waypoints + [destination]:
        segment_info = calculate_distance(current, next_point)
        segments.append(segment_info)
        total_distance += segment_info["distance_km"]
        current = next_point
    
    result = {
        "origin": origin,
        "destination": destination,
        "waypoints": waypoints,
        "total_distance_km": total_distance,
        "total_distance_miles": round(total_distance * 0.621371, 2),
        "segments": segments,
        "estimated_driving_time": f"{total_distance // 60}h {total_distance % 60}m"
    }
    
    print(f"[MAPS] Route from {origin} to {destination} via {len(waypoints)} waypoints: {total_distance} km")
    return result


def get_nearby_places(location: str, place_type: str, radius_km: int = 5) -> List[Dict[str, Any]]:
    """
    Find nearby places of a specific type.
    
    Args:
        location: Center location
        place_type: Type of place (e.g., 'restaurant', 'hotel', 'attraction')
        radius_km: Search radius in kilometers
    
    Returns:
        List of nearby places
    """
    # Simulated nearby places
    places = [
        {
            "name": f"Nearby {place_type.title()} 1",
            "type": place_type,
            "distance_km": radius_km * 0.3,
            "location": location,
            "rating": 4.5
        },
        {
            "name": f"Nearby {place_type.title()} 2",
            "type": place_type,
            "distance_km": radius_km * 0.6,
            "location": location,
            "rating": 4.2
        },
        {
            "name": f"Nearby {place_type.title()} 3",
            "type": place_type,
            "distance_km": radius_km * 0.9,
            "location": location,
            "rating": 4.0
        }
    ]
    
    print(f"[MAPS] Found {len(places)} {place_type}s near {location} within {radius_km}km")
    return places
