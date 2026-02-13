from ..state import AgentState

def researcher_node(state: AgentState):
    print("--- RESEARCHING ---")
    '''
    Research the web for prices, time taken and routes, return the different parameters to the validator.
    '''
    # Logic: Call APIs (Tavily, Google Maps, etc.)
    
    return {"current_total_cost": 1200, "itinerary": [{"item": "Flight", "price": 1200}]}