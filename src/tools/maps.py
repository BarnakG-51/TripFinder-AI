"""
Maps tool for calculating distances and travel times between locations.
This tool simulates map/distance calculation functionality.
"""
import os
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

def calculate_distance(origin: str, destination: str) -> Dict[str, Any]:
    """
    Calculate distance between two locations.
    
    Args:
        origin: Starting location
        destination: Destination location
    
    Returns:
        Dictionary with distance and travel time information
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_MAPS_API_KEY not set")
    
    url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if data['status'] != 'OK':
        raise ValueError(f"Google Maps API error: {data['status']}")
    
    # Extract distance in km
    distance = data['rows'][0]['elements'][0]['distance']['value'] / 1000  # meters to km
    return distance

def calculate_total_distance(travel_spots: List[str]) -> float:
    """
    Calculate total distance for a list of travel spots (assuming sequential travel).
    """
    total_distance = 0.0
    for i in range(len(travel_spots) - 1):
        total_distance += calculate_distance(travel_spots[i], travel_spots[i+1])
    return total_distance

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
        distance_km = calculate_distance(current, next_point)  # returns float
        segments.append({"from": current, "to": next_point, "distance_km": round(distance_km, 2)})
        total_distance += distance_km
        current = next_point

    AVG_DRIVING_SPEED_KMH = 60
    time_hours = total_distance / AVG_DRIVING_SPEED_KMH
    hours = int(time_hours)
    minutes = int((time_hours - hours) * 60)

    result = {
        "origin": origin,
        "destination": destination,
        "waypoints": waypoints,
        "total_distance_km": total_distance,
        "total_distance_miles": round(total_distance * 0.621371, 2),
        "segments": segments,
        "estimated_driving_time": f"{hours}h {minutes:02d}m"
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
