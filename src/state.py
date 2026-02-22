from typing import Annotated, TypedDict, List, Union, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # 'messages' stores the conversation history. 
    # add_messages is a helper that appends new messages rather than overwriting them.
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Structured data for the trip
    destination: str
    budget: float
    current_total_cost: float
    
    # Plan from the planner to be sent to researcher
    plan: Optional[dict]
    
    # The actual plan being built
    itinerary: List[dict] 
    
    # Internal flags to guide the logic
    is_valid: bool
    errors: List[str]