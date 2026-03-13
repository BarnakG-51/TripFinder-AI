from ..state import AgentState
from ..tools.search import search_hotels, search_flights, search_travel_spots, search_restaurants, search_item_price, SearchError
from ..tools.finance import calculate_total_cost
from ..tools.maps import calculate_total_distance


def _search_named_category(names: list, destination: str, category: str, errors: list, budget: float = None) -> list:
    """
    Search prices for each named item in the category.
    Returns results sorted low to high by the category-appropriate price field.
    Individual failures are appended to the shared errors list.
    Returns an empty list if all searches fail (caller should fall back to broad search).
    """
    price_key = {"hotel": "price_per_night", "restaurant": "price_per_person", "activity": "entry_fee"}[category]
    results = []
    for item_name in names:
        try:
            result = search_item_price(item_name, destination, category, budget=budget)
            results.append(result)
            print(f"[RESEARCHER] {category} '{item_name}': ${result.get(price_key, '?')}")
        except Exception as e:
            err_msg = f"Named {category} search failed for '{item_name}': {str(e)}"
            print(f"[RESEARCHER WARNING] {err_msg}")
            errors.append(err_msg)
    if results:
        results.sort(key=lambda x: x.get(price_key) or float("inf"))
        print(f"[RESEARCHER] {category}s sorted by price: {[r.get(price_key) for r in results]}")
    return results


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
            preferences=flight_params.get("preferences", "cheapest"),
            round_trip=True
        )
    except Exception as e:
        error_msg = f"Flight search failed: {str(e)}"
        print(f"[RESEARCHER ERROR] {error_msg}")
        errors.append(error_msg)

    # Extract multi-city route (if planner generated one)
    named_items = search_plan.get("named_items")
    route = (named_items or {}).get("route", [])
    destination = hotel_params.get("destination", state.get("destination", ""))

    if route:
        print(f"[RESEARCHER] Multi-city route: {[s['city'] for s in route]}")
        for stop in route:
            city = stop["city"]
            days_here = stop.get("days", 1)
            stop_hotel = stop.get("hotel", "")
            stop_activities = stop.get("activities", [])
            stop_restaurants = stop.get("restaurants", [])

            print(f"[RESEARCHER] Searching {city} ({days_here} nights)...")

            # Hotel for this city (named first, then broad fallback)
            city_hotels = []
            if stop_hotel:
                city_hotels = _search_named_category(
                    [stop_hotel], city, "hotel", errors,
                    budget=hotel_params.get("budget_per_night")
                )
            if not city_hotels:
                try:
                    city_hotels = search_hotels(
                        destination=city,
                        budget=hotel_params.get("budget_per_night", 150),
                        num_nights=days_here,
                        min_rating=hotel_params.get("min_rating", 3.0)
                    )[:1]
                except Exception as e:
                    errors.append(f"Hotel search failed for {city}: {e}")

            for h in city_hotels:
                h["city"] = city
                h["num_nights"] = days_here
            hotels.extend(city_hotels[:1])

            # Activities for this city (named first, then broad fallback)
            city_activities = []
            if stop_activities:
                city_activities = _search_named_category(
                    stop_activities, city, "activity", errors
                )
            if not city_activities:
                try:
                    city_activities = search_travel_spots(
                        destination=city,
                        interests=spot_params.get("interests", []),
                        budget=spot_params["budget"],
                        priority=spot_params.get("priority", "quality")
                    )
                except Exception as e:
                    errors.append(f"Activity search failed for {city}: {e}")
            for a in city_activities:
                a["city"] = city
            activities.extend(city_activities)

            # Restaurants for this city (named first, then broad fallback)
            city_restaurants = []
            if stop_restaurants:
                city_restaurants = _search_named_category(
                    stop_restaurants, city, "restaurant", errors
                )
            if not city_restaurants:
                try:
                    city_restaurants = search_restaurants(
                        destination=city,
                        cuisine=restaurant_params.get("cuisine"),
                        budget_per_meal=restaurant_params.get("budget_per_meal")
                    )
                except Exception as e:
                    errors.append(f"Restaurant search failed for {city}: {e}")
            for r in city_restaurants:
                r["city"] = city
            restaurants.extend(city_restaurants)

    else:
        # Single-city fallback (no LLM route available)
        # Search hotels — use named search if LLM provided names, else broad search
        if named_items and named_items.get("hotels"):
            print(f"[RESEARCHER] Using named hotel search for {len(named_items['hotels'])} items")
            hotels = _search_named_category(
                named_items["hotels"], destination, "hotel", errors,
                budget=hotel_params.get("budget_per_night")
            )
            if not hotels:
                print("[RESEARCHER] All named hotel searches failed — falling back to broad search")
                try:
                    hotels = search_hotels(
                        destination=hotel_params["destination"],
                        budget=hotel_params["budget_per_night"],
                        num_nights=num_nights,
                        min_rating=hotel_params.get("min_rating", 3.0)
                    )
                except Exception as e:
                    errors.append(f"Hotel fallback search failed: {str(e)}")
        else:
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

        # Search activities — use named search if LLM provided names, else broad search
        if named_items and named_items.get("activities"):
            print(f"[RESEARCHER] Using named activity search for {len(named_items['activities'])} items")
            activities = _search_named_category(named_items["activities"], destination, "activity", errors)
            if not activities:
                print("[RESEARCHER] All named activity searches failed — falling back to broad search")
                try:
                    activities = search_travel_spots(
                        destination=spot_params["destination"],
                        interests=spot_params.get("interests", []),
                        budget=spot_params["budget"],
                        priority=spot_params.get("priority", "quality")
                    )
                except Exception as e:
                    errors.append(f"Activity fallback search failed: {str(e)}")
        else:
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

        # Search restaurants — use named search if LLM provided names, else broad search
        if named_items and named_items.get("restaurants"):
            print(f"[RESEARCHER] Using named restaurant search for {len(named_items['restaurants'])} items")
            restaurants = _search_named_category(named_items["restaurants"], destination, "restaurant", errors)
            if not restaurants:
                print("[RESEARCHER] All named restaurant searches failed — falling back to broad search")
                try:
                    restaurants = search_restaurants(
                        destination=restaurant_params["destination"],
                        cuisine=restaurant_params.get("cuisine"),
                        budget_per_meal=restaurant_params.get("budget_per_meal")
                    )
                except Exception as e:
                    errors.append(f"Restaurant fallback search failed: {str(e)}")
        else:
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

    # Calculate inter-city transport distance using maps tool
    car_rental = {}
    if route and len(route) >= 2:
        try:
            cities = [stop["city"] for stop in route]
            dist = calculate_total_distance(cities)
            car_rental = {
                "total_distance_km": round(dist, 2),
                "per_km_cost": 0.50,
                "total_cost": round(dist * 0.50, 2),
                "route": " -> ".join(cities)
            }
        except Exception as e:
            errors.append(f"Inter-city distance calculation failed: {str(e)}")
    else:
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
        # Use outbound + return for round-trip total; fall back to outbound only if no return_price
        def flight_total(f):
            return f["price"] + f.get("return_price", 0)
        cost_items.append({"category": "flights", "price": min(flight_total(f) for f in flights)})
    if hotels:
        if any(h.get("num_nights") for h in hotels):
            # Multi-city: each hotel has its own num_nights
            hotel_cost = sum(
                (h.get("price_per_night") or 0) * h.get("num_nights", 1)
                for h in hotels
                if h.get("price_per_night") is not None
            )
            if hotel_cost > 0:
                cost_items.append({"category": "hotels", "price": hotel_cost})
        else:
            # Single-city: cheapest hotel * total nights
            valid_hotel_prices = [h["price_per_night"] for h in hotels if h.get("price_per_night") is not None]
            if valid_hotel_prices:
                cost_items.append({
                    "category": "hotels",
                    "price": min(valid_hotel_prices) * num_nights
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
