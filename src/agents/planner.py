import os
import json
import re
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import AgentState

# API keys loaded from Streamlit secrets via streamlit_app.py

# Budget allocation constants for plan variants
OPTIMIZED_BUDGET_PCT = 0.96  # 96% of budget
PREMIUM_BUDGET_PCT = 1.15    # 115% of budget
LOW_BUDGET_PCT = 0.50        # 50% of budget

def planner_node(state: AgentState):
    '''
    Generate THREE plan variants for the trip:
    1. Optimized Plan - Exact budget with slight money in hand (95-98% of budget)
    2. Premium Experience - Best amenities, slightly over budget (110-120% of budget)
    3. Low Budget - 50% of given budget
    
    Each plan includes hotels, flights, and travel spots selection.
    All three plans are sent to researcher for execution based on selected_plan.
    '''
    print("--- PLANNING (3 VARIANTS) ---")
    
    # Extract state information
    destination = state.get("destination", "Unknown")
    budget = state.get("budget", 5000)
    origin = state.get("origin", "New York")
    num_days = state.get("num_days", 5)
    # Ensure num_days is at least 1
    if num_days <= 0:
        num_days = 1
        print(f"[PLANNER] Warning: Invalid num_days, using default of 1")
    current_cost = state.get("current_total_cost", 0)
    replan_count = state.get("replan_count", 0)
    replan_errors = state.get("errors", [])

    # Select which plan to execute (default to optimized if not specified)
    selected_plan = state.get("selected_plan") or "optimized"

    # Auto-downgrade variant if replanning due to budget overrun
    if replan_count > 0 and any("Budget exceeded" in e for e in replan_errors):
        downgrade = {"premium": "optimized", "optimized": "low_budget"}
        if selected_plan in downgrade:
            new_plan = downgrade[selected_plan]
            print(f"[PLANNER] Downgrading {selected_plan} -> {new_plan} due to budget overrun")
            selected_plan = new_plan
    elif replan_count > 0:
        print(f"[PLANNER] REPLANNING (attempt {replan_count}) - Errors: {replan_errors}")
    
    print(f"[PLANNER] Creating 3 plan variants for {destination}")
    print(f"[PLANNER] Base budget: ${budget:.2f}, Duration: {num_days} days")
    
    # Create 3 different plan variants
    plan_variants = {}
    
    # 1. OPTIMIZED PLAN
    optimized_budget = budget * OPTIMIZED_BUDGET_PCT
    plan_variants["optimized"] = create_plan_for_budget(
        destination, origin, num_days, optimized_budget, 
        plan_type="optimized", original_budget=budget
    )
    print(f"[PLANNER] ✓ Optimized Plan: ${optimized_budget:.2f} ({OPTIMIZED_BUDGET_PCT*100:.0f}% of budget)")
    
    # 2. PREMIUM EXPERIENCE
    premium_budget = budget * PREMIUM_BUDGET_PCT
    plan_variants["premium"] = create_plan_for_budget(
        destination, origin, num_days, premium_budget,
        plan_type="premium", original_budget=budget
    )
    print(f"[PLANNER] ✓ Premium Plan: ${premium_budget:.2f} ({PREMIUM_BUDGET_PCT*100:.0f}% of budget)")
    
    # 3. LOW BUDGET
    low_budget = budget * LOW_BUDGET_PCT
    plan_variants["low_budget"] = create_plan_for_budget(
        destination, origin, num_days, low_budget,
        plan_type="low_budget", original_budget=budget
    )
    print(f"[PLANNER] ✓ Low Budget Plan: ${low_budget:.2f} ({LOW_BUDGET_PCT*100:.0f}% of budget)")
    
    print(f"[PLANNER] Selected plan for execution: {selected_plan}")
    
    # Get the search plan for the selected variant
    search_plan = plan_variants[selected_plan]

    # LLM-based named item generation for the selected plan only
    budget_alloc = search_plan.get("budget_allocation", {})
    named_items = _generate_named_items(
        destination=destination,
        plan_type=selected_plan,
        hotel_budget_per_night=search_plan["hotels"]["budget_per_night"],
        budget_per_meal=search_plan["restaurants"]["budget_per_meal"],
        activities_budget=budget_alloc.get("activities", 0),
        num_days=num_days
    )
    if named_items:
        search_plan["named_items"] = named_items
        print(f"[PLANNER] Added named_items to search_plan for {selected_plan} plan")
    else:
        # LLM route generation failed — try country→city resolution so the
        # researcher doesn't search against a country name like "France"
        fallback_city = _resolve_destination_to_city(destination)
        if fallback_city:
            search_plan["named_items"] = {
                "route": [{"city": fallback_city, "days": num_days,
                           "hotel": "", "restaurants": [], "activities": []}]
            }
            print(f"[PLANNER] LLM failed — fallback route: {destination} -> {fallback_city}")
        else:
            print(f"[PLANNER] No named_items — researcher will use broad search")

    return {
        "messages": [f"Planner: Created 3 plan variants for {destination} - executing {selected_plan} plan"],
        "plan_variants": plan_variants,
        "selected_plan": selected_plan,
        "search_plan": search_plan
    }


def create_plan_for_budget(destination, origin, num_days, budget, plan_type="optimized", original_budget=None):
    """
    Create a search plan for a specific budget allocation.
    
    Args:
        destination: Travel destination
        origin: Starting location
        num_days: Trip duration
        budget: Budget for this specific plan
        plan_type: "optimized", "premium", or "low_budget"
        original_budget: Original user budget (for reference)
    
    Returns:
        Dictionary with search plan details
    """
    # Adjust allocation percentages based on plan type
    if plan_type == "premium":
        # Premium: More on hotels; finer dining gets more meals budget
        flight_pct = 0.35
        hotel_pct = 0.40
        activities_pct = 0.15
        meals_pct = 0.10
    elif plan_type == "low_budget":
        # Low budget: Prioritize flights, economize on accommodation and dining
        flight_pct = 0.45
        hotel_pct = 0.30
        activities_pct = 0.15
        meals_pct = 0.10
    else:  # optimized
        # Optimized: Balanced allocation
        flight_pct = 0.40
        hotel_pct = 0.35
        activities_pct = 0.15
        meals_pct = 0.10

    flight_budget = budget * flight_pct
    hotel_budget = budget * hotel_pct
    activities_budget = budget * activities_pct
    meals_budget = budget * meals_pct

    # 2 meals per day (e.g. lunch + dinner); premium plans assume 3 meals
    meals_per_day = 3 if plan_type == "premium" else 2
    num_meals = num_days * meals_per_day
    budget_per_meal = meals_budget / num_meals if num_meals > 0 else 25.0

    return {
        "plan_type": plan_type,
        "target_budget": budget,
        "original_budget": original_budget or budget,
        "flights": {
            "origin": origin,
            "destination": destination,
            "budget": flight_budget,
            "search_required": True,
            "preferences": "direct" if plan_type == "premium" else "cheapest"
        },
        "hotels": {
            "destination": destination,
            "budget_per_night": hotel_budget / num_days,
            "num_nights": num_days,
            "total_budget": hotel_budget,
            "search_required": True,
            "min_rating": 4.5 if plan_type == "premium" else (3.5 if plan_type == "optimized" else 3.0)
        },
        "travel_spots": {
            "destination": destination,
            "budget": activities_budget,
            "interests": ["tourist attractions", "local experiences", "activities"],
            "search_required": True,
            "priority": "quality" if plan_type == "premium" else "value"
        },
        "restaurants": {
            "destination": destination,
            "budget_per_meal": round(budget_per_meal, 2),
            "num_meals": num_meals,
            "cuisine": "fine dining" if plan_type == "premium" else "local cuisine",
        },
        "budget_allocation": {
            "total_budget": budget,
            "original_budget": original_budget or budget,
            "budget_percentage": (budget / original_budget * 100) if original_budget else 100,
            "flights": flight_budget,
            "hotels": hotel_budget,
            "activities": activities_budget,
            "meals": meals_budget,
            "flight_pct": flight_pct * 100,
            "hotel_pct": hotel_pct * 100,
            "activities_pct": activities_pct * 100,
            "meals_pct": meals_pct * 100
        }
    }


def _extract_first_json_object(text: str) -> str | None:
    """
    Extract the first complete JSON object from text using brace counting.
    Handles nested structures correctly, unlike regex-based approaches.
    """
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return None


def _safe_parse_named_items(text: str):
    """
    Safely parse the LLM JSON response into a named_items dict with route structure.
    Returns the dict if valid, otherwise None.
    """
    def _coerce_stop(stop: dict) -> dict:
        """Coerce days to int in case the LLM returned a string."""
        if "days" in stop:
            try:
                stop["days"] = int(stop["days"])
            except (ValueError, TypeError):
                pass
        return stop

    def _validate(data):
        route = data.get("route")
        if not isinstance(route, list) or len(route) == 0:
            return False
        for stop in route:
            _coerce_stop(stop)
            if not isinstance(stop.get("city"), str):
                return False
            if not isinstance(stop.get("days"), int) or stop["days"] <= 0:
                return False
            if not isinstance(stop.get("hotel"), str):
                return False
            if not isinstance(stop.get("activities"), list) or len(stop["activities"]) == 0:
                return False
            if not isinstance(stop.get("restaurants"), list) or len(stop["restaurants"]) == 0:
                return False
        return True

    # Layer 1: direct JSON parse
    try:
        data = json.loads(text)
        if _validate(data):
            return data
    except (json.JSONDecodeError, TypeError):
        pass

    # Layer 2: brace-counting extraction (handles markdown fences and trailing text)
    extracted = _extract_first_json_object(text)
    if extracted:
        try:
            data = json.loads(extracted)
            if _validate(data):
                return data
        except (json.JSONDecodeError, TypeError):
            pass

    print("[PLANNER] Could not parse LLM response as valid named_items JSON")
    return None


# Mapping of common country names to their main tourist city
# Used as fallback when LLM route generation fails
_COUNTRY_TO_CITY = {
    "france": "Paris", "italy": "Rome", "spain": "Barcelona",
    "germany": "Berlin", "japan": "Tokyo", "china": "Beijing",
    "india": "Mumbai", "brazil": "Rio de Janeiro", "mexico": "Mexico City",
    "australia": "Sydney", "usa": "New York", "united states": "New York",
    "uk": "London", "united kingdom": "London", "england": "London",
    "canada": "Toronto", "thailand": "Bangkok", "greece": "Athens",
    "egypt": "Cairo", "morocco": "Marrakech", "portugal": "Lisbon",
    "netherlands": "Amsterdam", "switzerland": "Zurich", "austria": "Vienna",
    "czech republic": "Prague", "czechia": "Prague",
    "hungary": "Budapest", "poland": "Krakow", "turkey": "Istanbul",
    "south korea": "Seoul", "vietnam": "Hanoi", "indonesia": "Bali",
    "malaysia": "Kuala Lumpur", "peru": "Lima", "argentina": "Buenos Aires",
    "colombia": "Cartagena", "south africa": "Cape Town", "kenya": "Nairobi",
    "israel": "Tel Aviv", "sweden": "Stockholm", "norway": "Oslo",
    "denmark": "Copenhagen", "ireland": "Dublin", "scotland": "Edinburgh",
    "new zealand": "Auckland", "singapore": "Singapore",
}


def _resolve_destination_to_city(destination: str) -> str:
    """
    If destination is a known country name, return its main tourist city.
    Returns the original destination unchanged if it is already a city.
    """
    return _COUNTRY_TO_CITY.get(destination.strip().lower(), "")


def _generate_named_items(destination: str, plan_type: str, hotel_budget_per_night: float,
                           budget_per_meal: float, activities_budget: float, num_days: int = 5):
    """
    Call Groq LLM to generate a multi-city route for the trip.
    Returns a dict with key 'route' (list of city stops), each containing:
      city, days, hotel, restaurants, activities
    Returns None if the LLM call or JSON parse fails.
    """

    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("[PLANNER] GROQ_API_KEY not set — skipping LLM name generation")
        return None

    tier_labels = {"premium": "luxury", "optimized": "mid-range", "low_budget": "budget"}
    tier = tier_labels.get(plan_type, "mid-range")

    # Scale number of cities to trip length
    if num_days <= 3:
        cities_note = "1 city/area (short trip — do not split across cities)"
    elif num_days <= 7:
        cities_note = "2 different cities or nearby regions"
    else:
        cities_note = "2 to 3 different cities or regions"

    acts_per_city = max(2, (num_days // max(1, 1 if num_days <= 3 else (2 if num_days <= 7 else 3))) * 2)

    system_message = SystemMessage(content=(
        "You are a travel planning expert with deep knowledge of real establishments worldwide. "
        "Return a JSON object only — no markdown fences, no explanation, no extra text. "
        "All names must be real, currently operating places appropriate for the destination and budget tier. "
        "The hotel at each stop must be in the same city/area as that stop's activities."
    ))
    user_message = HumanMessage(content=(
        f"Generate a {num_days}-day {tier} trip itinerary for {destination}.\n"
        f"Budget context: Hotel ~${hotel_budget_per_night:.0f}/night, "
        f"Restaurant ~${budget_per_meal:.0f}/person, Activities total ${activities_budget:.0f}.\n"
        f"Route: {cities_note}. Days across all stops must sum to {num_days}.\n"
        f"Each stop: 1 real hotel (near its activities), 2 real restaurants, ~{acts_per_city} real activities.\n"
        f'Respond with exactly:\n'
        f'{{"route":[{{"city":"CityName","days":N,"hotel":"Real Hotel Name",'
        f'"restaurants":["Real R1","Real R2"],"activities":["Real A1","Real A2","Real A3"]}}]}}'
    ))

    try:
        llm = ChatGroq(
            api_key=groq_api_key,
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            max_tokens=768
        )
        response = llm.invoke([system_message, user_message])
        raw_text = response.content.strip()
        print(f"[PLANNER] LLM response (first 400 chars): {raw_text[:400]}")
        named_items = _safe_parse_named_items(raw_text)
        if named_items is None:
            print("[PLANNER] LLM JSON parse failed — falling back to broad search")
        else:
            cities = [s["city"] for s in named_items["route"]]
            print(f"[PLANNER] Route: {' -> '.join(cities)} ({len(named_items['route'])} stops)")
        return named_items
    except Exception as e:
        print(f"[PLANNER] LLM call failed: {e} — falling back to broad search")
        return None

