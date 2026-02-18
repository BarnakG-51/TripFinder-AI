from ..state import AgentState

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
    
    # Select which plan to execute (default to optimized if not specified)
    selected_plan = state.get("selected_plan") or "optimized"
    
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
        # Premium: More on hotels and activities for better experience
        flight_pct = 0.35
        hotel_pct = 0.40
        activities_pct = 0.25
    elif plan_type == "low_budget":
        # Low budget: Prioritize flights, economize on accommodation
        flight_pct = 0.45
        hotel_pct = 0.30
        activities_pct = 0.25
    else:  # optimized
        # Optimized: Balanced allocation
        flight_pct = 0.40
        hotel_pct = 0.35
        activities_pct = 0.25
    
    flight_budget = budget * flight_pct
    hotel_budget = budget * hotel_pct
    activities_budget = budget * activities_pct
    
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
            "interests": ["tourist attractions", "restaurants", "activities"],
            "search_required": True,
            "priority": "quality" if plan_type == "premium" else "value"
        },
        "budget_allocation": {
            "total_budget": budget,
            "original_budget": original_budget or budget,
            "budget_percentage": (budget / original_budget * 100) if original_budget else 100,
            "flight_allocation": flight_budget,
            "hotel_allocation": hotel_budget,
            "activities_allocation": activities_budget,
            "flight_pct": flight_pct * 100,
            "hotel_pct": hotel_pct * 100,
            "activities_pct": activities_pct * 100
        }
    }

