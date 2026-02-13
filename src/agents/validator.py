from ..state import AgentState

def validator_node(state: AgentState):
    print("--- VALIDATING ---")
    # Logic: Check if cost > budget
    if state["current_total_cost"] > state["budget"]:
        return {"is_valid": False, "errors": ["Budget exceeded!"]}
    return {"is_valid": True}