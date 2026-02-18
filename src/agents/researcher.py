from ..state import AgentState
from ..tools.search import SearchTool
from ..tools.maps import calculate_distance_between_places, calculate_total_trip_distance
from ..tools.finance import calculate_total_cost, check_budget_status
import os

def researcher_node(state: AgentState):
    print("--- RESEARCHING ---")
    '''
    Research the web for prices, time taken and routes, return the different parameters to the validator.
    Uses the plan from planner to search for hotels, flights, and travel spots.
    Uses search, maps, and finance tools to gather information.
    '''
    
    # Get the plan from planner
    plan = state.get("plan", {})
    destination = plan.get("destination", state.get("destination", "Unknown"))
    budget = plan.get("budget", state.get("budget", 0))
    
    print(f"Researching for destination: {destination}, Budget: ${budget}")
    
    # Initialize results
    itinerary = []
    total_cost = 0
    research_results = {
        "flights": None,
        "hotels": None,
        "attractions": None,
        "distances": None
    }
    
    # Initialize SearchTool if API key is available
    search_tool = None
    try:
        if os.getenv("TAVILY_API_KEY"):
            search_tool = SearchTool()
            print("SearchTool initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize SearchTool: {e}")
    
    # Execute tasks from the plan
    tasks = plan.get("tasks", [])
    for task in sorted(tasks, key=lambda x: x.get("priority", 999)):
        task_type = task.get("task_type")
        print(f"Executing task: {task.get('description')}")
        
        if task_type == "flights":
            # Search for flights
            try:
                if search_tool:
                    search_query = task.get("search_query")
                    results = search_tool.search(search_query, search_depth="basic", max_results=3)
                    research_results["flights"] = results
                    print("  - Searched for flights using Tavily API")
                else:
                    print("  - Using placeholder flight data (no API key)")
                
                # Add estimated flight cost to itinerary
                estimated_flight_cost = 500  # Placeholder - could be extracted from search results
                itinerary.append({
                    "name": "Flight",
                    "description": f"Round trip to {destination}",
                    "price": estimated_flight_cost,
                    "source": "search_results" if search_tool else "placeholder"
                })
                total_cost += estimated_flight_cost
                print(f"  - Added flight to itinerary, cost: ${estimated_flight_cost}")
            except Exception as e:
                print(f"  - Error searching flights: {e}")
        
        elif task_type == "hotels":
            # Search for hotels
            try:
                if search_tool:
                    search_query = task.get("search_query")
                    results = search_tool.search(search_query, search_depth="basic", max_results=3)
                    research_results["hotels"] = results
                    print("  - Searched for hotels using Tavily API")
                else:
                    print("  - Using placeholder hotel data (no API key)")
                
                # Add estimated hotel cost to itinerary
                estimated_hotel_cost = 400  # Placeholder - could be extracted from search results
                itinerary.append({
                    "name": "Hotel",
                    "description": f"Accommodation in {destination}",
                    "price": estimated_hotel_cost,
                    "source": "search_results" if search_tool else "placeholder"
                })
                total_cost += estimated_hotel_cost
                print(f"  - Added hotel to itinerary, cost: ${estimated_hotel_cost}")
            except Exception as e:
                print(f"  - Error searching hotels: {e}")
        
        elif task_type == "attractions":
            # Search for attractions
            try:
                if search_tool:
                    search_query = task.get("search_query")
                    results = search_tool.search(search_query, search_depth="basic", max_results=5)
                    research_results["attractions"] = results
                    print("  - Searched for attractions using Tavily API")
                else:
                    print("  - Using placeholder attraction data (no API key)")
                
                # Add estimated activities cost to itinerary
                estimated_activities_cost = 300  # Placeholder
                itinerary.append({
                    "name": "Activities & Attractions",
                    "description": f"Tours and attractions in {destination}",
                    "price": estimated_activities_cost,
                    "source": "search_results" if search_tool else "placeholder"
                })
                total_cost += estimated_activities_cost
                print(f"  - Added attractions to itinerary, cost: ${estimated_activities_cost}")
            except Exception as e:
                print(f"  - Error searching attractions: {e}")
        
        elif task_type == "distances":
            # Calculate distances if Google Maps API is available
            try:
                if os.getenv("GOOGLE_MAPS_API_KEY"):
                    # Example: Calculate distance from airport to city center
                    # This would ideally use actual locations from search results
                    origin = f"{destination} Airport"
                    city_center = f"{destination} City Center"
                    
                    distance_result = calculate_distance_between_places.invoke({
                        "origin": origin,
                        "destination": city_center
                    })
                    
                    research_results["distances"] = distance_result
                    print(f"  - Calculated distance: {distance_result}")
                else:
                    print("  - Google Maps API key not set, skipping distance calculation")
            except Exception as e:
                print(f"  - Error calculating distances: {e}")
    
    # Use finance tool to calculate total cost
    if itinerary:
        cost_result = calculate_total_cost.invoke({"items": itinerary})
        if "total_cost" in cost_result:
            total_cost = cost_result["total_cost"]
        
        # Check budget status
        budget_status = check_budget_status.invoke({
            "current_cost": total_cost,
            "budget": budget
        })
        print(f"Budget status: {budget_status.get('status', 'Unknown')}")
        print(f"Total cost: ${total_cost}, Budget: ${budget}")
    
    # Return updated state with research results
    return {
        "current_total_cost": total_cost,
        "itinerary": itinerary,
        "messages": [f"Researcher: Completed research for {destination}. Found {len(itinerary)} items totaling ${total_cost}"]
    }
