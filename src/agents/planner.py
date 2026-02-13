from ..state import AgentState

def planner_node(state: AgentState):
    '''
    Generate a plan for the trip using LLM and select hotels, flights, and travel spots which fit in the budget
    and also the time limit specified by the user.
    '''
    print("--- PLANNING ---")
    # Logic: LLM breaks down the request
    return {"messages": ["Planner: I need to find flights and hotels."]}
