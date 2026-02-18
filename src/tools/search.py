"""
Search tool for finding hotels, flights, and travel spots.
This tool simulates web search functionality for travel-related queries.
"""

from typing import List, Dict, Any


def search_hotels(destination: str, budget: float, check_in: str = None, check_out: str = None) -> List[Dict[str, Any]]:
    """
    Search for hotels at the destination within budget.
    
    Args:
        destination: The location to search for hotels
        budget: Maximum price per night
        check_in: Check-in date (optional)
        check_out: Check-out date (optional)
    
    Returns:
        List of hotel options with prices and details
    """
    # Simulated search results
    hotels = [
        {
            "name": f"Hotel Grand {destination}",
            "price_per_night": min(budget * 0.6, 150),
            "rating": 4.5,
            "amenities": ["WiFi", "Pool", "Breakfast"],
            "location": destination
        },
        {
            "name": f"{destination} City Inn",
            "price_per_night": min(budget * 0.4, 100),
            "rating": 4.0,
            "amenities": ["WiFi", "Parking"],
            "location": destination
        },
        {
            "name": f"Budget Stay {destination}",
            "price_per_night": min(budget * 0.3, 75),
            "rating": 3.5,
            "amenities": ["WiFi"],
            "location": destination
        }
    ]
    
    print(f"[SEARCH] Found {len(hotels)} hotels in {destination}")
    return hotels


def search_flights(origin: str, destination: str, budget: float, date: str = None) -> List[Dict[str, Any]]:
    """
    Search for flights from origin to destination within budget.
    
    Args:
        origin: Departure location
        destination: Arrival location
        budget: Maximum ticket price
        date: Travel date (optional)
    
    Returns:
        List of flight options with prices and details
    """
    # Simulated search results
    flights = [
        {
            "airline": "SkyHigh Airlines",
            "price": min(budget * 0.7, 450),
            "duration": "3h 30m",
            "stops": 0,
            "departure": "08:00 AM",
            "arrival": "11:30 AM",
            "route": f"{origin} -> {destination}"
        },
        {
            "airline": "BudgetAir",
            "price": min(budget * 0.5, 320),
            "duration": "5h 15m",
            "stops": 1,
            "departure": "06:00 AM",
            "arrival": "11:15 AM",
            "route": f"{origin} -> {destination}"
        },
        {
            "airline": "QuickFly",
            "price": min(budget * 0.6, 380),
            "duration": "4h 00m",
            "stops": 0,
            "departure": "02:00 PM",
            "arrival": "06:00 PM",
            "route": f"{origin} -> {destination}"
        }
    ]
    
    print(f"[SEARCH] Found {len(flights)} flights from {origin} to {destination}")
    return flights


def search_travel_spots(destination: str, interests: List[str] = None) -> List[Dict[str, Any]]:
    """
    Search for travel spots and attractions at the destination.
    
    Args:
        destination: The location to search for attractions
        interests: List of interest categories (e.g., museums, parks, restaurants)
    
    Returns:
        List of travel spots with details
    """
    interests = interests or ["tourist attractions", "restaurants", "activities"]
    
    # Simulated search results
    spots = [
        {
            "name": f"{destination} Historic Museum",
            "category": "museum",
            "rating": 4.7,
            "entry_fee": 15,
            "description": f"Famous museum in {destination}",
            "estimated_time": "2-3 hours"
        },
        {
            "name": f"{destination} Central Park",
            "category": "park",
            "rating": 4.8,
            "entry_fee": 0,
            "description": f"Beautiful park in {destination}",
            "estimated_time": "1-2 hours"
        },
        {
            "name": f"Local Cuisine Restaurant",
            "category": "restaurant",
            "rating": 4.6,
            "entry_fee": 0,
            "avg_meal_price": 30,
            "description": f"Authentic local food in {destination}",
            "estimated_time": "1-2 hours"
        },
        {
            "name": f"{destination} Adventure Tours",
            "category": "activity",
            "rating": 4.5,
            "entry_fee": 50,
            "description": f"Guided tours in {destination}",
            "estimated_time": "3-4 hours"
        }
    ]
    
    print(f"[SEARCH] Found {len(spots)} travel spots in {destination}")
    return spots
