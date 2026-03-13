"""
Search tool for finding hotels, flights, and travel spots.
This tool simulates web search functionality for travel-related queries.
"""

from typing import List, Dict, Any, Optional
import os
from tavily import TavilyClient
import json
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    raise EnvironmentError(
        "[ERROR] TAVILY_API_KEY not found in environment variables. "
        "Please set it in your .env file or export it: export TAVILY_API_KEY='your_key'"
    )

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
        star_label = "luxury" if min_rating >= 4.5 else ("4-star" if min_rating >= 4.0 else "3-star")
        query = f"best {star_label} hotel in {destination} under ${int(budget)} per night review"
        if check_in and check_out:
            query += f" available {check_in} to {check_out}"

        print(f"[SEARCH] Searching hotels with Tavily: {query}")

        #Perform Tavily Search
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_domains=["booking.com", "hotels.com", "tripadvisor.com", "agoda.com"]
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
                   date: str = None,
                   round_trip: bool = True) -> List[Dict[str, Any]]:
    """
    Search for flights from origin to destination within budget.

    Args:
        origin: Departure location
        destination: Arrival location
        budget: Maximum ticket price (one-way)
        date: Travel date (optional)
        round_trip: If True, also search return leg and add return_price (default True)

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
        query = f"flights from {origin} to {destination} under ${int(budget)}"
        if preferences == "direct":
            query += " direct non-stop"
        elif preferences == "fastest":
            query += " fastest shortest duration"
        else:
            query += " cheapest economy class"

        if date:
            query += f" on {date}"
        print(f"[SEARCH] Searching flights with Tavily: {query}")

        # Perform Tavily search (outbound)
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_domains=["kayak.com", "skyscanner.com", "expedia.com", "momondo.com"]
        )

        # Check if we got results
        if not response.get("results"):
            raise SearchError(
                f"No flights found from {origin} to {destination} within budget ${budget}. "
                f"Try increasing your budget or checking for different dates."
            )

        # Parse outbound results
        flights = _parse_flight_results(response, origin, destination, budget)

        if not flights:
            raise SearchError(
                f"Could not parse flight results from {origin} to {destination}. "
                f"The search returned {len(response.get('results', []))} results but none matched criteria."
            )

        # Search return leg if round_trip requested
        if round_trip:
            return_query = f"flights from {destination} to {origin} under ${int(budget)}"
            if preferences == "direct":
                return_query += " direct non-stop"
            elif preferences == "fastest":
                return_query += " fastest shortest duration"
            else:
                return_query += " cheapest economy class"
            print(f"[SEARCH] Searching return flights with Tavily: {return_query}")
            try:
                return_response = tavily_client.search(
                    query=return_query,
                    search_depth="advanced",
                    max_results=5,
                    include_domains=["kayak.com", "skyscanner.com", "expedia.com", "momondo.com"]
                )
                return_flights = _parse_flight_results(return_response, destination, origin, budget)
                # Attach return price to each outbound flight (pair by index, fallback to cheapest)
                cheapest_return = min((rf["price"] for rf in return_flights), default=None)
                for i, flight in enumerate(flights):
                    if i < len(return_flights):
                        flight["return_price"] = return_flights[i]["price"]
                    elif cheapest_return is not None:
                        flight["return_price"] = cheapest_return
                    else:
                        flight["return_price"] = flight["price"]
                    flight["return_route"] = f"{destination} -> {origin}"
                print(f"[SEARCH] ✓ Attached return prices to {len(flights)} outbound flights")
            except Exception as e:
                print(f"[SEARCH] Warning: Return flight search failed ({e}), estimating from outbound price")
                for flight in flights:
                    flight["return_price"] = round(flight["price"] * 0.95, 2)
                    flight["return_route"] = f"{destination} -> {origin}"

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


def search_restaurants(
    destination: str,
    cuisine: str = None,
    budget_per_meal: float = None,
    num_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Search for restaurants and dining options at the destination.

    Args:
        destination: City/location to search in
        cuisine: Optional cuisine type filter (e.g. "Italian", "local")
        budget_per_meal: Optional max price per person
        num_results: How many results to retrieve

    Returns:
        List of restaurant options with prices and details
    """
    if not destination:
        raise SearchError("Destination is required for restaurant search.")

    try:
        query = f"best restaurants in {destination}"
        if cuisine:
            query += f" {cuisine} cuisine"
        if budget_per_meal:
            query += f" under ${int(budget_per_meal)} per person"
        else:
            query += " highly rated must try"

        print(f"[SEARCH] Searching restaurants with Tavily: {query}")

        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=num_results,
            include_domains=["tripadvisor.com", "yelp.com", "timeout.com", "thefork.com"]
        )

        if not response.get("results"):
            raise SearchError(f"No restaurants found in {destination}.")

        restaurants = _parse_restaurant_results(response, destination)

        if not restaurants:
            raise SearchError(
                f"Could not parse restaurant results for {destination}. "
                f"The search returned {len(response.get('results', []))} results but none matched criteria."
            )

        print(f"[SEARCH] Found {len(restaurants)} restaurants in {destination}")
        return restaurants

    except SearchError:
        raise
    except Exception as e:
        raise SearchError(
            f"Restaurant search failed for {destination}: {str(e)}. "
            f"Check your Tavily API key and internet connection."
        ) from e


def search_item_price(name: str, destination: str, category: str, budget: float = None) -> Dict[str, Any]:
    """
    Search for the price of a specific named hotel, restaurant, or activity.

    Args:
        name:        The real name of the establishment or attraction.
        destination: City/country for search context.
        category:    Must be "hotel", "restaurant", or "activity".
        budget:      Optional budget hint used as fallback when no price is extracted.

    Returns:
        A dict in the same shape as the corresponding broad-search result:
          hotel      -> {name, price_per_night, rating, amenities, location, url, description}
          restaurant -> {name, cuisine_type, price_per_person, rating, location, url, description}
          activity   -> {name, category, rating, entry_fee, description, url, location}

    Raises:
        SearchError: if Tavily returns no results or the category is invalid.
    """
    if not name or not destination:
        raise SearchError("Both name and destination are required for search_item_price.")

    if category == "hotel":
        query = f"{name} {destination} hotel price per night room rate"
        domains = ["booking.com", "hotels.com", "tripadvisor.com", "agoda.com"]
    elif category == "restaurant":
        query = f"{name} {destination} restaurant price per person menu cost"
        domains = ["tripadvisor.com", "yelp.com", "thefork.com", "timeout.com"]
    elif category == "activity":
        query = f"{name} {destination} admission ticket price entry fee"
        domains = ["viator.com", "tripadvisor.com", "getyourguide.com", "timeout.com"]
    else:
        raise SearchError(
            f"Invalid category '{category}'. Must be 'hotel', 'restaurant', or 'activity'."
        )

    print(f"[SEARCH] Named price search — {category}: '{name}' in {destination}")
    try:
        response = tavily_client.search(
            query=query,
            search_depth="advanced",
            max_results=3,
            include_domains=domains
        )
        if not response.get("results"):
            raise SearchError(f"No results for {category} '{name}' in {destination}.")
        return _parse_named_item_result(response, name, destination, category, budget=budget)
    except SearchError:
        raise
    except Exception as e:
        raise SearchError(
            f"Named price search failed for {category} '{name}' in {destination}: {str(e)}"
        ) from e


# ============ RESULT PARSERS ============

def _parse_hotel_results(response: Dict, destination: str, budget: float, min_rating: float) -> List[Dict[str, Any]]:
    """Parse Tavily search results into hotel format."""
    hotels = []

    for idx, result in enumerate(response.get("results", [])[:5]):
        try:
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")

            # Extract hotel name by stripping booking-site branding from title
            name = _clean_title(title)

            # Try to extract real price from content, fall back to budget estimate
            real_price = _extract_price_per_night(content)
            estimated_price = real_price if real_price else round(min(budget * (0.6 + idx * 0.1), budget), 2)

            hotel = {
                "name": name,
                "price_per_night": estimated_price,
                "rating": _extract_rating(content) or (min_rating + (0.5 if "luxury" in content.lower() else 0)),
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


def _parse_restaurant_results(response: Dict, destination: str) -> List[Dict[str, Any]]:
    """Parse Tavily search results into restaurant format."""
    restaurants = []

    for idx, result in enumerate(response.get("results", [])[:10]):
        try:
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")

            restaurant = {
                "name": _clean_title(title),
                "cuisine_type": _extract_cuisine(title, content),
                "price_per_person": _extract_meal_price(content),
                "rating": _extract_rating(content),
                "location": destination,
                "url": url,
                "description": content[:200] + "..." if len(content) > 200 else content
            }
            restaurants.append(restaurant)
        except Exception as e:
            print(f"[SEARCH] Warning: Failed to parse restaurant result {idx}: {e}")
            continue

    return restaurants


def _parse_named_item_result(response: Dict, name: str, destination: str, category: str, budget: float = None) -> Dict[str, Any]:
    """
    Parse a Tavily named-search result into the category-appropriate dict shape.
    Uses the best (first) result, then aggregates across all results for price accuracy.
    """
    best = response["results"][0]
    content = best.get("content", "")
    url = best.get("url", "")
    description = content[:200] + "..." if len(content) > 200 else content
    rating = _extract_rating(content) or 4.0

    if category == "hotel":
        prices = [_extract_price_per_night(r.get("content", "")) for r in response["results"]]
        prices = [p for p in prices if p]
        if prices:
            price = sorted(prices)[len(prices) // 2]
        elif budget:
            price = round(budget * 0.7, 2)
        else:
            price = None
        return {
            "name": name,
            "price_per_night": round(price, 2) if price is not None else None,
            "rating": rating,
            "amenities": _extract_amenities(content),
            "location": destination,
            "url": url,
            "description": description
        }

    elif category == "restaurant":
        price = _extract_meal_price(content)
        if price == 25.0:  # default — try other results
            for r in response["results"][1:]:
                p = _extract_meal_price(r.get("content", ""))
                if p != 25.0:
                    price = p
                    break
        return {
            "name": name,
            "cuisine_type": _extract_cuisine(name, content),
            "price_per_person": round(price, 2),
            "rating": rating,
            "location": destination,
            "url": url,
            "description": description
        }

    else:  # activity
        fee = _extract_fee(content)
        if fee == 15.0:  # default — try other results
            for r in response["results"][1:]:
                f = _extract_fee(r.get("content", ""))
                if f != 15.0:
                    fee = f
                    break
        return {
            "name": name,
            "category": "activity",
            "rating": rating,
            "entry_fee": round(fee, 2),
            "description": description,
            "url": url,
            "location": destination
        }


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
    airlines = ["Delta", "United", "American", "Southwest", "JetBlue", "Spirit", "Frontier", "IndiGo", "AirIndia", "AirIndiaExpress", "AkasaAir"]
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


def _clean_title(title: str) -> str:
    """Strip booking-site branding from page titles to get the property/restaurant name."""
    import re
    # Remove common site suffixes: "- Booking.com", "| TripAdvisor", "– Hotels.com", etc.
    name = re.split(r'\s*[-|–—]\s*(?:booking\.com|tripadvisor|hotels\.com|agoda|yelp|timeout|thefork)', title, flags=re.IGNORECASE)[0]
    # Also split on standalone " - " and " | " as a fallback
    for sep in [" - ", " | ", " – "]:
        if sep in name:
            name = name.split(sep)[0]
    return name.strip() or title.strip()


def _extract_price_per_night(content: str) -> Optional[float]:
    """Try to extract an explicit per-night price from hotel content."""
    import re
    patterns = [
        # "$120 per night", "$120/night"
        r'\$\s*(\d+(?:\.\d{2})?)\s*(?:per\s*night|/\s*night)',
        # "$120 a night", "$120 nightly"
        r'\$\s*(\d+(?:\.\d{2})?)\s*(?:a\s*night|nightly)',
        # "from $120", "starting at $120", "starting from $120"
        r'(?:from|starting\s+at|starting\s+from)\s+\$\s*(\d+(?:\.\d{2})?)',
        # "120 USD per night", "120 USD/night"
        r'(\d+(?:\.\d{2})?)\s*USD\s*(?:per\s*night|/\s*night|nightly)',
        # "rate of $120", "price of $120", "cost of $120"
        r'(?:rate|price|cost)\s+of\s+\$\s*(\d+(?:\.\d{2})?)',
        # "average nightly rate $120"
        r'(?:average\s+)?nightly\s+(?:rate|price)\s+\$\s*(\d+(?:\.\d{2})?)',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return float(match.group(1))
    return None


def _extract_cuisine(title: str, content: str) -> str:
    """Identify cuisine type from restaurant title and content."""
    combined = (title + " " + content).lower()
    cuisine_map = {
        "italian": ["italian", "pizza", "pasta", "trattoria", "osteria"],
        "french": ["french", "brasserie", "bistro", "patisserie"],
        "japanese": ["japanese", "sushi", "ramen", "izakaya", "tempura"],
        "chinese": ["chinese", "dim sum", "cantonese", "sichuan"],
        "indian": ["indian", "curry", "tandoor", "masala", "biryani"],
        "mexican": ["mexican", "tacos", "burrito", "cantina"],
        "thai": ["thai", "pad thai", "tom yum"],
        "american": ["american", "burger", "bbq", "diner", "steakhouse"],
        "mediterranean": ["mediterranean", "greek", "lebanese", "hummus"],
        "local": ["local", "traditional", "authentic", "regional", "classic"],
    }
    for cuisine, keywords in cuisine_map.items():
        if any(kw in combined for kw in keywords):
            return cuisine.title()
    return "International"


def _extract_meal_price(content: str) -> float:
    """Extract average price per person from restaurant content."""
    import re
    # Look for explicit per-person pricing
    match = re.search(
        r'\$\s*(\d+(?:\.\d{2})?)\s*(?:per\s*person|pp|each|per\s*head)',
        content,
        re.IGNORECASE
    )
    if match:
        return float(match.group(1))
    # Fall back to any dollar amount in a reasonable meal-price range ($5-$150)
    prices = re.findall(r'\$(\d+(?:\.\d{2})?)', content)
    meal_prices = [float(p) for p in prices if 5 <= float(p) <= 150]
    if meal_prices:
        return round(min(meal_prices), 2)
    return 25.0  # default fallback

