from ..state import AgentState
from ..tools.search import search_hotels, search_flights, search_travel_spots, search_restaurants, SearchError
from ..tools.finance import calculate_total_cost
from ..tools.maps import calculate_total_distance


def researcher_node(state: AgentState):
    '''
    Research the web for prices, time taken and routes, return the different parameters to the validator.

    This node executes the search plan created by the planner using search, maps, and finance tools.
    It looks up actual prices and distances for hotels, flights, travel spots, and restaurants.
    '''
    print("--- RESEARCHING ---")

    # Get the search plan from planner
    search_plan = state.get("search_plan", {})
    budget = state.get("budget", 5000)

    if not search_plan:
        error_msg = "[RESEARCHER] No search plan found, using default values"
        return {
            "messages": [f"Researcher error: {error_msg}"],
            "research_results": {
                "flights": [],
                "hotels": [],
                "activities": [],
                "restaurants": [],
                "car_rental": {},
                "cost_breakdown": {}
            },
            "search_errors": [error_msg]
        }

    plan_type = search_plan.get("plan_type", "optimized")
    print(f"[RESEARCHER] Executing {plan_type} plan with Tavily API")

    errors = []
    flights = []
    hotels = []
    activities = []
    restaurants = []

    # Hoist params before try blocks so they're always defined
    flight_params = search_plan.get("flights", {})
    hotel_params = search_plan.get("hotels", {})
    spot_params = search_plan.get("travel_spots", {})
    restaurant_params = search_plan.get("restaurants", {})
    num_nights = hotel_params.get("num_nights", state.get("num_days", 5))

    # Search flights with error handling
    try:
        flights = search_flights(
            origin=flight_params["origin"],
            destination=flight_params["destination"],
            budget=flight_params["budget"],
            preferences=flight_params.get("preferences", "cheapest")
        )
    except Exception as e:
        error_msg = f"Flight search failed: {str(e)}"
        print(f"[RESEARCHER ERROR] {error_msg}")
        errors.append(error_msg)

    # Search hotels with error handling
    try:
        hotels = search_hotels(
            destination=hotel_params["destination"],
            budget=hotel_params["budget_per_night"],
            num_nights=num_nights,
            min_rating=hotel_params.get("min_rating", 3.0)
        )
    except Exception as e:
        error_msg = f"Hotel search failed: {str(e)}"
        print(f"[RESEARCHER ERROR] {error_msg}")
        errors.append(error_msg)

    # Search activities with error handling
    try:
        activities = search_travel_spots(
            destination=spot_params["destination"],
            interests=spot_params.get("interests", []),
            budget=spot_params["budget"],
            priority=spot_params.get("priority", "quality")
        )
    except Exception as e:
        error_msg = f"Activity search failed: {str(e)}"
        print(f"[RESEARCHER ERROR] {error_msg}")
        errors.append(error_msg)

    # Search restaurants with error handling
    try:
        restaurants = search_restaurants(
            destination=restaurant_params["destination"],
            cuisine=restaurant_params.get("cuisine"),
            budget_per_meal=restaurant_params.get("budget_per_meal")
        )
    except Exception as e:
        error_msg = f"Restaurant search failed: {str(e)}"
        print(f"[RESEARCHER ERROR] {error_msg}")
        errors.append(error_msg)

    # Check if we have any results at all
    if not flights and not hotels and not activities and not restaurants:
        combined_error = " | ".join(errors)
        return {
            "messages": ["Researcher: All searches failed"],
            "research_results": {
                "flights": [],
                "hotels": [],
                "activities": [],
                "restaurants": [],
                "car_rental": {},
                "cost_breakdown": {}
            },
            "search_errors": [f"Complete search failure: {combined_error}"] if combined_error else errors
        }

    # Calculate car rental cost using maps tool
    car_rental = {}
    locations = [a.get("location", "") for a in activities if a.get("location")]
    if len(locations) >= 2:
        try:
            dist = calculate_total_distance(locations)
            car_rental = {
                "total_distance_km": round(dist, 2),
                "per_km_cost": 0.50,
                "total_cost": round(dist * 0.50, 2)
            }
        except Exception as e:
            errors.append(f"Car rental calculation failed: {str(e)}")

    # Build cost items and delegate to finance tool
    cost_items = []
    if flights:
        cost_items.append({"category": "flights", "price": min(f["price"] for f in flights)})
    if hotels:
        cost_items.append({
            "category": "hotels",
            "price": min(h["price_per_night"] for h in hotels) * num_nights
        })
    for activity in activities[:5]:
        cost_items.append({"category": "activities", "price": activity.get("entry_fee", 0)})
    if car_rental:
        cost_items.append({"category": "other", "price": car_rental.get("total_cost", 0)})
    if restaurants:
        num_meals = restaurant_params.get("num_meals", state.get("num_days", 5) * 2)
        avg_meal_price = sum(r.get("price_per_person", 25.0) for r in restaurants[:5]) / min(len(restaurants), 5)
        cost_items.append({"category": "meals", "price": round(avg_meal_price * num_meals, 2)})

    cost_breakdown = calculate_total_cost(cost_items)
    total_cost = cost_breakdown["total_cost"]

    print(f"[RESEARCHER] Total estimated cost: ${total_cost:.2f}")

    # Build success message
    success_parts = []
    if flights:
        success_parts.append(f"{len(flights)} flights")
    if hotels:
        success_parts.append(f"{len(hotels)} hotels")
    if activities:
        success_parts.append(f"{len(activities)} activities")
    if restaurants:
        success_parts.append(f"{len(restaurants)} restaurants")

    message = f"Researcher: Found {', '.join(success_parts)} for {plan_type} plan"
    if errors:
        message += f" (with {len(errors)} partial failures)"

    return {
        "messages": [message],
        "research_results": {
            "flights": flights,
            "hotels": hotels,
            "activities": activities,
            "restaurants": restaurants,
            "car_rental": car_rental,
            "cost_breakdown": cost_breakdown
        },
        "search_errors": errors if errors else None
    }
