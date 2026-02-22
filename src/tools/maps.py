import os
from typing import List, Dict
import googlemaps
from langchain_core.tools import tool


@tool
def calculate_distance_between_places(origin: str, destination: str) -> Dict:
    """
    Calculate distance and duration between two places using Google Maps API.
    
    Args:
        origin: Starting location (address, place name, or coordinates)
        destination: Ending location (address, place name, or coordinates)
    
    Returns:
        Dictionary with distance (km), duration (minutes), and route details
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable not set"}
    
    try:
        gmaps = googlemaps.Client(key=api_key)
        result = gmaps.distance_matrix(
            origins=[origin],
            destinations=[destination],
            mode="driving"
        )
        
        if result['rows'][0]['elements'][0]['status'] == 'OK':
            element = result['rows'][0]['elements'][0]
            distance_km = element['distance']['value'] / 1000
            duration_min = element['duration']['value'] / 60
            
            return {
                "origin": origin,
                "destination": destination,
                "distance_km": round(distance_km, 2),
                "duration_minutes": round(duration_min, 2),
                "distance_text": element['distance']['text'],
                "duration_text": element['duration']['text']
            }
        else:
            return {"error": f"Could not find route between {origin} and {destination}"}
    except Exception as e:
        return {"error": str(e)}


@tool
def calculate_total_trip_distance(locations: List[str]) -> Dict:
    """
    Calculate total distance and duration for a trip with multiple stops.
    
    Args:
        locations: List of locations in order (minimum 2 locations)
    
    Returns:
        Dictionary with total distance, duration, and leg-by-leg breakdown
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable not set"}
    
    if len(locations) < 2:
        return {"error": "Need at least 2 locations to calculate trip distance"}
    
    try:
        gmaps = googlemaps.Client(key=api_key)
        
        total_distance_km = 0
        total_duration_min = 0
        legs = []
        
        for i in range(len(locations) - 1):
            origin = locations[i]
            destination = locations[i + 1]
            
            result = gmaps.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode="driving"
            )
            
            if result['rows'][0]['elements'][0]['status'] == 'OK':
                element = result['rows'][0]['elements'][0]
                distance_km = element['distance']['value'] / 1000
                duration_min = element['duration']['value'] / 60
                
                total_distance_km += distance_km
                total_duration_min += duration_min
                
                legs.append({
                    "leg": i + 1,
                    "from": origin,
                    "to": destination,
                    "distance_km": round(distance_km, 2),
                    "duration_minutes": round(duration_min, 2)
                })
            else:
                return {"error": f"Could not find route between {origin} and {destination}"}
        
        return {
            "total_locations": len(locations),
            "total_distance_km": round(total_distance_km, 2),
            "total_duration_minutes": round(total_duration_min, 2),
            "total_duration_hours": round(total_duration_min / 60, 2),
            "legs": legs
        }
    except Exception as e:
        return {"error": str(e)}
