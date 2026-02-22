"""
Search tool for finding hotels, flights, and travel spots.
This tool simulates web search functionality for travel-related queries.
"""

from typing import List, Dict, Any, Optional
import os
from tavily import TavilyClient
import json

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise EnvironmentError
    ("[ERROR] TAVILY_API_KEY not found in environment variables."
     "Please set it in your .env file or export it: export TAVILY_API_KEY='your_key'")
    tavily_client = None

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)
class SearchError(Exception):
    pass

def search_hotels(destination: str, 
                  budget: float, 
                  num_nights: int = 1,
                  min_rating: float = 3.0,
                  check_in: str = None, 
                  check_out: str = None) -> List[Dict[str, Any]]:
    """
    Search for hotels at the destination within budget.
    
    Args:
        destination: The location to search for hotels
        budget: Maximum price per night
        num_nights: Number of nights
        min_rating: Minimum hotel rating
        check_in: Check-in date (optional)
        check_out: Check-out date (optional)
    
    Returns:
        List of hotel options with prices and details
    """
    if not destination:
        raise SearchError("Destination is required for hotel search.")
    
    if budget<=0:
        raise SearchError(f"Invalid budget: ${budget}. Budget must be positive.")
    
    try:
        query = f"hotels in {destination} under ${budget} per night rating above {min_rating}"
        if check_in and check_out:
            query += f"from {check_in} to {check_out}"

        print(f"[SEARCH] Searching hotels with Tavily: {query}")


        #Perform Tavily Search
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_domains=["booking.com", "agoda.com", "makemytrip.com", "tripadvisor.com"]
        )

        #Check if we got search results
        if not response.get("results"):
            raise SearchError(
                f"No hotels found in {destination} within budget ${budget}/night"
                f"Try increasing your budget or choosing a different destination."
            )
        
        #Parse Results
        hotels = _parse_hotel_results(response, destination, budget, min_rating)

        if not hotels:
            raise SearchError(
                f"Could not parse hotel results for {destination}"
                f"The search returned {len(response.get('results', []))}"
            )
        
        print(f"[SEARCH] Found {len(hotels)} hotels in {destination}")
        return hotels
    except SearchError:
        raise
    except Exception as e:
        raise SearchError(
            f"Hotel search failed for {destination}: {str(e)}."
            f"Check your Tavily API key and internet connection"
        )

def search_flights(origin: str, 
                   destination: str, 
                   budget: float,
                   preferences: str = "cheapest", 
                   date: str = None) -> List[Dict[str, Any]]:
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
    # Error Handling
    
    if not origin or not destination:
        raise SearchError("Both origin and destination are required for flight search.")
    if budget <= 0:
        raise SearchError(f"Invalid budget: ${budget}. Budget must be positive.")
    if preferences not in ["cheapest", "direct", "fastest"]:
        raise SearchError(f"Invalid preference: {preferences}. Must be 'cheapest, 'direct' or 'fastest'")
    
    try:
        query = f"flights from {origin} to {destination} under ${budget}"
        if preferences == "direct":
            query += "direct non-stop"
        elif preferences == "fastest":
            query += "fastest"
        else:
            query+="cheapest"
        
        if date:
            query += f"on {date}"
        print(f"[SEARCH] Searching flights with Tavily: {query}")
        
        # Perform Tavily search
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_domains=["google.com/flights", "kayak.com", "skyscanner.com", "expedia.com"]
        )
        
        # Check if we got results
        if not response.get("results"):
            raise SearchError(
                f"No flights found from {origin} to {destination} within budget ${budget}. "
                f"Try increasing your budget or checking for different dates."
            )
        
        # Parse results
        flights = _parse_flight_results(response, origin, destination, budget)
        
        if not flights:
            raise SearchError(
                f"Could not parse flight results from {origin} to {destination}. "
                f"The search returned {len(response.get('results', []))} results but none matched criteria."
            )
        
        print(f"[SEARCH] ✓ Found {len(flights)} flights from {origin} to {destination}")
        return flights
        
    except SearchError:
        raise
    except Exception as e:
        raise SearchError(
            f"Flight search failed from {origin} to {destination}: {str(e)}. "
            f"Check your Tavily API key and internet connection."
        ) from e


def search_travel_spots(
    destination: str, 
    interests: List[str] = None,
    budget: float = None,
    priority: str = "quality"
) -> List[Dict[str, Any]]:
    """
    Search for travel spots and attractions at the destination using Tavily API.
    
    Args:
        destination: The location to search for attractions
        interests: List of interest categories
        budget: Optional budget for activities
        priority: "quality" or "value"
    
    Returns:
        List of travel spots with details
    
    Raises:
        SearchError: If search fails or no results found
    """
    interests = interests or ["tourist attractions", "restaurants", "activities"]
    
    if not destination:
        raise SearchError("Destination is required for travel spot search")
    
    if priority not in ["quality", "value"]:
        raise SearchError(f"Invalid priority: {priority}. Must be 'quality' or 'value'")
    
    try:
        # Construct search query
        query = f"top {', '.join(interests)} in {destination}"
        if priority == "value":
            query += " budget friendly"
        else:
            query += " highly rated"
        
        if budget:
            query += f" under ${budget}"
        
        print(f"[SEARCH] Searching travel spots with Tavily: {query}")
        
        # Perform Tavily search
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=10,
            include_domains=["tripadvisor.com", "lonelyplanet.com", "timeout.com", "viator.com"]
        )
        
        # Check if we got results
        if not response.get("results"):
            raise SearchError(
                f"No travel spots found in {destination} for interests: {', '.join(interests)}. "
                f"Try different interest categories or destination."
            )
        
        # Parse results
        spots = _parse_travel_spot_results(response, destination, interests)
        
        if not spots:
            raise SearchError(
                f"Could not parse travel spot results for {destination}. "
                f"The search returned {len(response.get('results', []))} results but none matched criteria."
            )
        
        print(f"[SEARCH] ✓ Found {len(spots)} travel spots in {destination}")
        return spots
        
    except SearchError:
        raise
    except Exception as e:
        raise SearchError(
            f"Travel spot search failed for {destination}: {str(e)}. "
            f"Check your Tavily API key and internet connection."
        ) from e


# ============ RESULT PARSERS ============

def _parse_hotel_results(response: Dict, destination: str, budget: float, min_rating: float) -> List[Dict[str, Any]]:
    """Parse Tavily search results into hotel format."""
    hotels = []
    
    for idx, result in enumerate(response.get("results", [])[:5]):
        try:
            # Extract information from Tavily result
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")
            
            # Estimate price based on budget
            price_factor = 0.6 + (idx * 0.1)
            estimated_price = min(budget * price_factor, budget)
            
            hotel = {
                "name": title.split("|")[0].strip() if "|" in title else title,
                "price_per_night": round(estimated_price, 2),
                "rating": min_rating + (0.5 if "luxury" in content.lower() else 0),
                "amenities": _extract_amenities(content),
                "location": destination,
                "url": url,
                "description": content[:200] + "..." if len(content) > 200 else content
            }
            hotels.append(hotel)
        except Exception as e:
            print(f"[SEARCH] Warning: Failed to parse hotel result {idx}: {e}")
            continue
    
    return hotels


def _parse_flight_results(response: Dict, origin: str, destination: str, budget: float) -> List[Dict[str, Any]]:
    """Parse Tavily search results into flight format."""
    flights = []
    
    for idx, result in enumerate(response.get("results", [])[:5]):
        try:
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")
            
            # Estimate price
            price_factor = 0.5 + (idx * 0.1)
            estimated_price = min(budget * price_factor, budget)
            
            flight = {
                "airline": _extract_airline(title, content),
                "price": round(estimated_price, 2),
                "duration": _extract_duration(content),
                "stops": _extract_stops(content),
                "route": f"{origin} -> {destination}",
                "url": url,
                "description": content[:200] + "..." if len(content) > 200 else content
            }
            flights.append(flight)
        except Exception as e:
            print(f"[SEARCH] Warning: Failed to parse flight result {idx}: {e}")
            continue
    
    return flights


def _parse_travel_spot_results(response: Dict, destination: str, interests: List[str]) -> List[Dict[str, Any]]:
    """Parse Tavily search results into travel spot format."""
    spots = []
    
    for idx, result in enumerate(response.get("results", [])[:10]):
        try:
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")
            
            spot = {
                "name": title.split("|")[0].strip() if "|" in title else title,
                "category": _categorize_spot(title, content, interests),
                "rating": _extract_rating(content),
                "entry_fee": _extract_fee(content),
                "description": content[:300] + "..." if len(content) > 300 else content,
                "url": url,
                "location": destination
            }
            spots.append(spot)
        except Exception as e:
            print(f"[SEARCH] Warning: Failed to parse travel spot result {idx}: {e}")
            continue
    
    return spots


# ============ HELPER FUNCTIONS ============

def _extract_amenities(content: str) -> List[str]:
    """Extract amenities from content text."""
    amenities = []
    amenity_keywords = ["wifi", "pool", "breakfast", "parking", "gym", "spa", "restaurant"]
    
    content_lower = content.lower()
    for keyword in amenity_keywords:
        if keyword in content_lower:
            amenities.append(keyword.capitalize())
    
    return amenities or ["WiFi"]


def _extract_airline(title: str, content: str) -> str:
    """Extract airline name from title or content."""
    airlines = ["Delta", "United", "American", "Southwest", "JetBlue", "Spirit", "Frontier"]
    for airline in airlines:
        if airline.lower() in title.lower() or airline.lower() in content.lower():
            return airline
    return "Various Airlines"


def _extract_duration(content: str) -> str:
    """Extract flight duration from content."""
    import re
    duration_match = re.search(r'(\d+)h\s*(\d+)?m?', content)
    if duration_match:
        hours = duration_match.group(1)
        minutes = duration_match.group(2) or "00"
        return f"{hours}h {minutes}m"
    return "~4h 30m"


def _extract_stops(content: str) -> int:
    """Extract number of stops from content."""
    if "non-stop" in content.lower() or "direct" in content.lower():
        return 0
    elif "1 stop" in content.lower():
        return 1
    elif "2 stop" in content.lower():
        return 2
    return 0


def _categorize_spot(title: str, content: str, interests: List[str]) -> str:
    """Categorize a travel spot based on interests."""
    combined = (title + " " + content).lower()
    
    if "museum" in combined:
        return "museum"
    elif "park" in combined or "garden" in combined:
        return "park"
    elif "restaurant" in combined or "food" in combined or "dining" in combined:
        return "restaurant"
    elif "tour" in combined or "activity" in combined:
        return "activity"
    
    return interests[0] if interests else "attraction"


def _extract_rating(content: str) -> float:
    """Extract rating from content."""
    import re
    rating_match = re.search(r'(\d+\.?\d*)\s*(?:stars?|rating|out of 5)', content, re.IGNORECASE)
    if rating_match:
        return float(rating_match.group(1))
    return 4.0


def _extract_fee(content: str) -> float:
    """Extract entry fee from content."""
    import re
    fee_match = re.search(r'\$(\d+(?:\.\d{2})?)', content)
    if fee_match:
        return float(fee_match.group(1))
    
    if "free" in content.lower():
        return 0.0
    
    return 15.0

