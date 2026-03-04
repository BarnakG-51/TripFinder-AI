from ..state import AgentState
from ..tools.finance import check_budget


def validator_node(state: AgentState):
    print("--- VALIDATING ---")

    rr = state.get("research_results") or {}
    flights = rr.get("flights", [])
    hotels = rr.get("hotels", [])
    activities = rr.get("activities", [])
    car_rental = rr.get("car_rental", {})
    cost_breakdown = rr.get("cost_breakdown", {})
    budget = state.get("budget", 0)
    replan_count = state.get("replan_count", 0)
    search_errors = state.get("search_errors") or []
    num_nights = state.get("num_days", 1)

    errors = []

    # Structural validation — check that research produced usable results
    if not flights:
        errors.append("No flights found. Try a higher budget or different origin/destination.")
    if not hotels:
        errors.append("No hotels found. Try a higher budget or different destination.")
    if not activities:
        errors.append("No activities found.")
    errors.extend([f"Search error: {e}" for e in search_errors])

    # Budget check via finance tool
    total_cost = cost_breakdown.get("total_cost", 0.0)
    budget_info = check_budget(current_cost=total_cost, budget=budget)
    if not budget_info["within_budget"]:
        overage = total_cost - budget
        errors.append(
            f"Budget exceeded by ${overage:.2f} "
            f"(${total_cost:.2f} estimated vs ${budget:.2f} budget)"
        )

    # Build itinerary from best research results
    itinerary = []

    if flights:
        best_flight = min(flights, key=lambda f: f["price"])
        itinerary.append({
            "type": "flight",
            "name": f"Flight: {best_flight.get('route', 'Origin -> Destination')}",
            "cost": best_flight["price"],
            "airline": best_flight.get("airline"),
            "duration": best_flight.get("duration"),
            "stops": best_flight.get("stops", 0),
            "url": best_flight.get("url", "")
        })

    if hotels:
        best_hotel = min(hotels, key=lambda h: h["price_per_night"])
        itinerary.append({
            "type": "hotel",
            "name": best_hotel.get("name", "Hotel"),
            "cost": round(best_hotel["price_per_night"] * num_nights, 2),
            "price_per_night": best_hotel["price_per_night"],
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
