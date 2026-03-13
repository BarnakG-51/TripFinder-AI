from ..state import AgentState
from ..tools.finance import check_budget


def _build_day_by_day_itinerary(route, flights, hotels, activities, restaurants, car_rental):
    """
    Build a structured day-by-day itinerary from multi-city route data.
    Each item has a 'day' and 'city' field for ordered display.
    """
    itinerary = []

    # Index research results by city
    hotels_by_city = {}
    activities_by_city = {}
    restaurants_by_city = {}

    for h in hotels:
        city = h.get("city", "")
        hotels_by_city.setdefault(city, []).append(h)
    for a in activities:
        city = a.get("city", "")
        activities_by_city.setdefault(city, []).append(a)
    for r in restaurants:
        city = r.get("city", "")
        restaurants_by_city.setdefault(city, []).append(r)

    current_day = 1

    # Day 1: arrival flight
    if flights:
        best_flight = min(flights, key=lambda f: f.get("price", 0) + f.get("return_price", 0))
        itinerary.append({
            "type": "flight",
            "subtype": "arrival",
            "day": current_day,
            "name": f"Arrive: {best_flight.get('route', 'Origin -> Destination')}",
            "airline": best_flight.get("airline"),
            "duration": best_flight.get("duration"),
            "stops": best_flight.get("stops", 0),
            "cost": best_flight.get("price", 0),
            "url": best_flight.get("url", "")
        })

    # One hotel check-in + activities + restaurants per city stop
    for i, stop in enumerate(route):
        city = stop["city"]
        days_here = stop.get("days", 1)
        is_last = (i == len(route) - 1)

        # Check in at the hotel for this city
        city_hotels = hotels_by_city.get(city, [])
        if city_hotels:
            best_hotel = min(city_hotels, key=lambda h: h.get("price_per_night") or float("inf"))
            price_pn = best_hotel.get("price_per_night") or 0
            itinerary.append({
                "type": "hotel",
                "subtype": "check_in",
                "day": current_day,
                "city": city,
                "name": best_hotel.get("name", f"Hotel in {city}"),
                "cost": round(price_pn * days_here, 2),
                "price_per_night": price_pn,
                "num_nights": days_here,
                "rating": best_hotel.get("rating"),
                "amenities": best_hotel.get("amenities", []),
                "url": best_hotel.get("url", "")
            })

        city_activities = activities_by_city.get(city, [])
        city_restaurants = restaurants_by_city.get(city, [])
        acts_per_day = max(1, len(city_activities) // days_here)

        for day_offset in range(days_here):
            day_num = current_day + day_offset
            day_acts = city_activities[day_offset * acts_per_day: (day_offset + 1) * acts_per_day]

            for act in day_acts:
                itinerary.append({
                    "type": "activity",
                    "day": day_num,
                    "city": city,
                    "name": act.get("name", "Activity"),
                    "cost": act.get("entry_fee", 0),
                    "rating": act.get("rating"),
                    "category": act.get("category", "attraction"),
                    "description": (act.get("description") or "")[:150],
                    "url": act.get("url", "")
                })

            if city_restaurants:
                rest = city_restaurants[day_offset % len(city_restaurants)]
                itinerary.append({
                    "type": "restaurant",
                    "day": day_num,
                    "city": city,
                    "name": rest.get("name", "Restaurant"),
                    "cost": rest.get("price_per_person", 25.0),
                    "cuisine_type": rest.get("cuisine_type", "International"),
                    "rating": rest.get("rating"),
                    "description": (rest.get("description") or "")[:150],
                    "url": rest.get("url", "")
                })

        current_day += days_here

        # Travel to next city
        if not is_last:
            next_city = route[i + 1]["city"]
            itinerary.append({
                "type": "transport",
                "subtype": "inter_city",
                "day": current_day,
                "name": f"Travel: {city} to {next_city}",
                "city": next_city,
                "from_city": city,
                "to_city": next_city,
                "cost": 0
            })

    # Distribute car rental cost across inter-city transport legs
    if car_rental.get("total_cost"):
        transport_legs = [item for item in itinerary if item.get("subtype") == "inter_city"]
        if transport_legs:
            cost_per_leg = round(car_rental["total_cost"] / len(transport_legs), 2)
            for item in transport_legs:
                item["cost"] = cost_per_leg
                item["distance_km"] = round(
                    car_rental.get("total_distance_km", 0) / len(transport_legs), 1
                )
        else:
            itinerary.append({
                "type": "transport",
                "day": current_day,
                "name": "Transport",
                "cost": car_rental["total_cost"],
                "total_distance_km": car_rental.get("total_distance_km", 0)
            })

    # Return flight on last day
    if flights:
        best_flight = min(flights, key=lambda f: f.get("price", 0) + f.get("return_price", 0))
        return_price = best_flight.get("return_price") or best_flight.get("price", 0)
        return_route = best_flight.get("return_route") or best_flight.get("route", "")
        itinerary.append({
            "type": "flight",
            "subtype": "departure",
            "day": current_day,
            "name": f"Depart: {return_route}",
            "airline": best_flight.get("airline"),
            "cost": return_price,
            "url": best_flight.get("url", "")
        })

    return itinerary


def validator_node(state: AgentState):
    print("--- VALIDATING ---")

    rr = state.get("research_results") or {}
    flights = rr.get("flights", [])
    hotels = rr.get("hotels", [])
    activities = rr.get("activities", [])
    restaurants = rr.get("restaurants", [])
    car_rental = rr.get("car_rental", {})
    cost_breakdown = rr.get("cost_breakdown", {})
    budget = state.get("budget", 0)
    replan_count = state.get("replan_count", 0)
    search_errors = state.get("search_errors") or []
    num_nights = state.get("num_days", 1)

    errors = []

    # Structural validation
    if not flights:
        errors.append("No flights found. Try a higher budget or different origin/destination.")
    if not hotels:
        errors.append("No hotels found. Try a higher budget or different destination.")
    if not activities:
        errors.append("No activities found.")
    errors.extend([f"Search error: {e}" for e in search_errors])

    # Budget check
    total_cost = cost_breakdown.get("total_cost", 0.0)
    budget_info = check_budget(current_cost=total_cost, budget=budget)
    if not budget_info["within_budget"]:
        overage = total_cost - budget
        errors.append(
            f"Budget exceeded by ${overage:.2f} "
            f"(${total_cost:.2f} estimated vs ${budget:.2f} budget)"
        )

    # Build itinerary — day-by-day if multi-city route data is available
    route = ((state.get("search_plan") or {}).get("named_items") or {}).get("route", [])
    has_multi_city = route and any(item.get("city") for item in hotels + activities + restaurants)

    if has_multi_city:
        print(f"[VALIDATOR] Building day-by-day itinerary for {len(route)} city stops")
        itinerary = _build_day_by_day_itinerary(route, flights, hotels, activities, restaurants, car_rental)
    else:
        # Flat itinerary fallback (single-city or no route data)
        itinerary = []

        if flights:
            best_flight = min(flights, key=lambda f: f.get("price", 0) + f.get("return_price", 0))
            return_price = best_flight.get("return_price")
            total_flight_cost = best_flight.get("price", 0) + (return_price or 0)
            flight_entry = {
                "type": "flight",
                "name": f"Flight: {best_flight.get('route', 'Origin -> Destination')}",
                "cost": round(total_flight_cost, 2),
                "outbound_price": best_flight.get("price"),
                "airline": best_flight.get("airline"),
                "duration": best_flight.get("duration"),
                "stops": best_flight.get("stops", 0),
                "url": best_flight.get("url", "")
            }
            if return_price is not None:
                flight_entry["return_price"] = return_price
                flight_entry["return_route"] = best_flight.get("return_route", "")
            itinerary.append(flight_entry)

        if hotels:
            valid_hotels = [h for h in hotels if h.get("price_per_night") is not None]
            if not valid_hotels:
                valid_hotels = hotels
            best_hotel = min(valid_hotels, key=lambda h: h.get("price_per_night") or float("inf"))
            price_per_night = best_hotel.get("price_per_night") or 0
            itinerary.append({
                "type": "hotel",
                "name": best_hotel.get("name", "Hotel"),
                "cost": round(price_per_night * num_nights, 2),
                "price_per_night": price_per_night,
                "num_nights": num_nights,
                "rating": best_hotel.get("rating"),
                "amenities": best_hotel.get("amenities", []),
                "url": best_hotel.get("url", "")
            })

        top_activities = sorted(activities, key=lambda a: a.get("rating", 0), reverse=True)[:5]
        for activity in top_activities:
            itinerary.append({
                "type": "activity",
                "name": activity.get("name", "Activity"),
                "cost": activity.get("entry_fee", 0),
                "rating": activity.get("rating"),
                "category": activity.get("category", "attraction"),
                "description": (activity.get("description") or "")[:150],
                "url": activity.get("url", "")
            })

        top_restaurants = sorted(restaurants, key=lambda r: r.get("rating", 0), reverse=True)[:3]
        for restaurant in top_restaurants:
            itinerary.append({
                "type": "restaurant",
                "name": restaurant.get("name", "Restaurant"),
                "cost": restaurant.get("price_per_person", 25.0),
                "cuisine_type": restaurant.get("cuisine_type", "International"),
                "rating": restaurant.get("rating"),
                "description": (restaurant.get("description") or "")[:150],
                "url": restaurant.get("url", "")
            })

        if car_rental.get("total_cost"):
            itinerary.append({
                "type": "transport",
                "name": "Car Rental",
                "cost": car_rental["total_cost"],
                "total_distance_km": car_rental.get("total_distance_km", 0),
                "per_km_cost": car_rental.get("per_km_cost", 0.50)
            })

    is_valid = len(errors) == 0
    new_replan_count = replan_count if is_valid else replan_count + 1

    if is_valid:
        print(f"[VALIDATOR] Plan validated. Total cost: ${total_cost:.2f} / ${budget:.2f}")
    else:
        print(f"[VALIDATOR] Validation failed (attempt {new_replan_count}): {errors}")

    return {
        "messages": [f"Validator: {'VALID' if is_valid else 'INVALID'} - ${total_cost:.2f}"],
        "is_valid": is_valid,
        "errors": errors,
        "itinerary": itinerary,
        "current_total_cost": total_cost,
        "replan_count": new_replan_count
    }
