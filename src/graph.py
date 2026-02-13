from langgraph.graph import StateGraph, END
from .state import AgentState

#--- NODE IMPORTS ---
from src.agents.planner import planner_node
from src.agents.researcher import researcher_node
from src.agents.validator import validator_node

# --- ROUTING LOGIC ---
def should_continue(state: AgentState):
    if state["is_valid"]:
        return "end"
    else:
        # If not valid, go back to the planner to fix the mistakes
        return "replan"

# --- GRAPH CONSTRUCTION ---
workflow = StateGraph(AgentState)

# 1. Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("researcher", researcher_node)
workflow.add_node("validator", validator_node)

# 2. Define the Flow (Edges)
workflow.set_entry_point("planner")
workflow.add_edge("planner", "researcher")
workflow.add_edge("researcher", "validator")

# 3. Add Conditional Edge (The "Brain")
workflow.add_conditional_edges(
    "validator",
    should_continue,
    {
        "replan": "planner",
        "end": END
    }
)

# 4. Compile the Graph
app = workflow.compile()