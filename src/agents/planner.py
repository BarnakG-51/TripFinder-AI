from ..state import AgentState

def planner_node(state: AgentState):
    '''
    Generate a plan for the trip using LLM and select hotels, flights, and travel spots which fit in the budget
    and also the time limit specified by the user.
    '''
    print("--- PLANNING ---")
    
    # Extract information from state
    destination = state.get("destination", "Unknown")
    budget = state.get("budget", 0)
    errors = state.get("errors", [])
    
    # Check if this is a replan (has errors from validator)
    if errors:
        print(f"Replanning due to errors: {errors}")
    
    # Create a structured plan with tasks for the researcher
    plan = {
        "destination": destination,
        "budget": budget,
        "tasks": [
            {
                "task_type": "flights",
                "description": f"Search for flights to {destination}",
                "search_query": f"best flight deals to {destination}",
                "priority": 1
            },
            {
                "task_type": "hotels",
                "description": f"Find hotels in {destination}",
                "search_query": f"best hotels in {destination}",
                "priority": 2
            },
            {
                "task_type": "attractions",
                "description": f"Identify travel spots and attractions in {destination}",
                "search_query": f"top attractions and places to visit in {destination}",
                "priority": 3
            },
            {
                "task_type": "distances",
                "description": f"Calculate distances between locations in {destination}",
                "priority": 4
            }
        ],
        "requirements": {
            "budget_constraint": budget,
            "optimize_for": "cost_and_experience"
        }
    }
    
    print(f"Plan created with {len(plan['tasks'])} tasks for destination: {destination}")
    
    return {
        "plan": plan,
        "messages": [f"Planner: Created plan to search for flights, hotels, and attractions in {destination} within budget of ${budget}"]
    }

