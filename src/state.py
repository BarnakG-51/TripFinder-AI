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
    origin: Optional[str]  # Starting location for flights
    num_days: Optional[int]  # Trip duration
    
    # The actual plan being built
    itinerary: List[dict] 
    
    # Plan from planner to be executed by researcher
    search_plan: Optional[dict]  # Contains specific search queries for hotels, flights, spots
    
    # Research results from researcher
    research_results: Optional[dict]  # Contains prices, distances, and options found
    
    # Internal flags to guide the logic
    is_valid: bool
    errors: List[str]