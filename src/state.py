from typing import Annotated, TypedDict, List, Union, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    # 'messages' stores the conversation history. 
    # add_messages is a helper that appends new messages rather than overwriting them.
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Raw user input
    user_prompt: Optional[str]  # Original user prompt
    
    # Structured data for the trip (extracted from prompt)
    destination: str
    budget: float
    current_total_cost: float
    origin: Optional[str]  # Starting location for flights
    num_days: Optional[int]  # Trip duration
    
    # The actual plan being built
    itinerary: List[dict] 
    
    # Plan variants from planner (3 different options)
    plan_variants: Optional[dict]  # Contains "optimized", "premium", "low_budget" plans
    
    # Selected plan variant (which one to execute)
    selected_plan: Optional[str]  # "optimized", "premium", or "low_budget"
    
    # Plan from planner to be executed by researcher
    search_plan: Optional[dict]  # Contains specific search queries for hotels, flights, spots
    
    # Research results from researcher
    research_results: Optional[dict]  # Contains prices, distances, and options found
    
    # Internal flags to guide the logic
    is_valid: bool
    errors: List[str]