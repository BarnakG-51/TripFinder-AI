from ..state import AgentState
from ..tools.search import search_hotels, search_flights, search_travel_spots
from ..tools.maps import calculate_distance, get_route
from ..tools.finance import calculate_total_cost, check_budget

def researcher_node(state: AgentState):
    '''
    Research the web for prices, time taken and routes, return the different parameters to the validator.
    
    This node executes the search plan created by the planner using search, maps, and finance tools.
    It looks up actual prices and distances for hotels, flights, and travel spots.
    '''
    print("--- RESEARCHING ---")
    
    # Get the search plan from planner
    search_plan = state.get("search_plan", {})
    budget = state.get("budget", 5000)
    
    if not search_plan:
        print("[RESEARCHER] No search plan found, using default values")
        return {
            "current_total_cost": 0,
            "itinerary": [],
            "research_results": {}
        }
    
    # Initialize results
    research_results = {
        "flights": [],
        "hotels": [],
        "travel_spots": [],
        "distances": {}
    }
    itinerary = []
    
    # 1. Search for flights
    if search_plan.get("flights", {}).get("search_required"):
        flight_plan = search_plan["flights"]
        origin = flight_plan.get("origin", "New York")
        destination = flight_plan.get("destination", "Unknown")
        flight_budget = flight_plan.get("budget", 1000)
        
        print(f"[RESEARCHER] Searching flights from {origin} to {destination}")
        flights = search_flights(origin, destination, flight_budget)
        research_results["flights"] = flights
        
        # Calculate distance for the flight route
        distance_info = calculate_distance(origin, destination)
        research_results["distances"]["flight_route"] = distance_info
        
        # Select best flight (cheapest direct flight or cheapest overall)
        best_flight = min(flights, key=lambda f: f["price"])
        itinerary.append({
            "category": "flights",
            "item": f"Flight: {best_flight['airline']}",
            "price": best_flight["price"],
            "details": best_flight
        })
        print(f"[RESEARCHER] Selected flight: {best_flight['airline']} at ${best_flight['price']:.2f}")
    
    # 2. Search for hotels
    if search_plan.get("hotels", {}).get("search_required"):
        hotel_plan = search_plan["hotels"]
        destination = hotel_plan.get("destination", "Unknown")
        budget_per_night = hotel_plan.get("budget_per_night", 100)
        num_nights = hotel_plan.get("num_nights", 3)
        
        print(f"[RESEARCHER] Searching hotels in {destination}")
        hotels = search_hotels(destination, budget_per_night)
        research_results["hotels"] = hotels
        
        # Select best hotel (best value - rating vs price)
        best_hotel = max(hotels, key=lambda h: h["rating"] / (h["price_per_night"] / 50))
        total_hotel_cost = best_hotel["price_per_night"] * num_nights
        itinerary.append({
            "category": "hotels",
            "item": f"Hotel: {best_hotel['name']} ({num_nights} nights)",
            "price": total_hotel_cost,
            "details": {**best_hotel, "num_nights": num_nights}
        })
        print(f"[RESEARCHER] Selected hotel: {best_hotel['name']} at ${best_hotel['price_per_night']:.2f}/night x {num_nights} nights = ${total_hotel_cost:.2f}")
    
    # 3. Search for travel spots
    if search_plan.get("travel_spots", {}).get("search_required"):
        spot_plan = search_plan["travel_spots"]
        destination = spot_plan.get("destination", "Unknown")
        interests = spot_plan.get("interests", [])
        activities_budget = spot_plan.get("budget", 500)
        
        print(f"[RESEARCHER] Searching travel spots in {destination}")
        travel_spots = search_travel_spots(destination, interests)
        research_results["travel_spots"] = travel_spots
        
        # Select activities within budget
        remaining_budget = activities_budget
        for spot in travel_spots:
            spot_cost = spot.get("entry_fee", 0) + spot.get("avg_meal_price", 0)
            if spot_cost <= remaining_budget:
                itinerary.append({
                    "category": "activities",
                    "item": f"Activity: {spot['name']}",
                    "price": spot_cost,
                    "details": spot
                })
                remaining_budget -= spot_cost
                print(f"[RESEARCHER] Added activity: {spot['name']} at ${spot_cost:.2f}")
    
    # Calculate total cost using finance tool
    cost_summary = calculate_total_cost(itinerary)
    total_cost = cost_summary["total_cost"]
    
    # Check budget
    budget_status = check_budget(total_cost, budget)
    
    print(f"[RESEARCHER] Research complete. Total cost: ${total_cost:.2f}")
    print(f"[RESEARCHER] Budget status: {budget_status['status']}")
    
    return {
        "current_total_cost": total_cost,
        "itinerary": itinerary,
        "research_results": research_results,
        "messages": [f"Researcher: Found options totaling ${total_cost:.2f}"]
    }
