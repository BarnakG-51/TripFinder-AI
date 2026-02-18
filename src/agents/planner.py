from ..state import AgentState

def planner_node(state: AgentState):
    '''
    Generate a plan for the trip using LLM and select hotels, flights, and travel spots which fit in the budget
    and also the time limit specified by the user.
    
    This node creates a structured search plan that will be executed by the researcher.
    '''
    print("--- PLANNING ---")
    
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
    
    # Calculate budget allocation (rule-based approach)
    remaining_budget = budget - current_cost
    
    # Allocate budget: 40% flights, 35% hotels, 25% activities/meals
    flight_budget = remaining_budget * 0.40
    hotel_budget = remaining_budget * 0.35
    activities_budget = remaining_budget * 0.25
    
    # Create structured search plan
    search_plan = {
        "flights": {
            "origin": origin,
            "destination": destination,
            "budget": flight_budget,
            "search_required": True
        },
        "hotels": {
            "destination": destination,
            "budget_per_night": hotel_budget / num_days,
            "num_nights": num_days,
            "total_budget": hotel_budget,
            "search_required": True
        },
        "travel_spots": {
            "destination": destination,
            "budget": activities_budget,
            "interests": ["tourist attractions", "restaurants", "activities"],
            "search_required": True
        },
        "budget_allocation": {
            "total_budget": budget,
            "remaining_budget": remaining_budget,
            "flight_allocation": flight_budget,
            "hotel_allocation": hotel_budget,
            "activities_allocation": activities_budget
        }
    }
    
    print(f"[PLANNER] Created plan for {destination}")
    print(f"[PLANNER] Budget allocation - Flights: ${flight_budget:.2f}, Hotels: ${hotel_budget:.2f}, Activities: ${activities_budget:.2f}")
    
    return {
        "messages": [f"Planner: Created search plan for {destination} with ${remaining_budget:.2f} budget"],
        "search_plan": search_plan
    }

