"""
Prompt Parser Node - Extracts structured information from user prompts using LLM.
This node analyzes user input and extracts destination, budget, origin, duration, etc.
"""

from ..state import AgentState
import re


def parse_prompt_node(state: AgentState):
    """
    Parse user prompt and extract structured trip information.
    
    Uses pattern matching and simple NLP to extract:
    - Destination
    - Budget
    - Origin (if specified)
    - Trip duration (number of days)
    - Preferences (if any)
    
    In production, this would use an LLM (like GPT-4) to intelligently parse
    complex natural language queries. For now, we use pattern matching.
    """
    print("--- PARSING PROMPT ---")
    
    user_prompt = state.get("user_prompt", "")
    
    if not user_prompt:
        # If no prompt, use existing state values
        print("[PARSER] No user prompt provided, using existing state values")
        return {
            "messages": ["Parser: Using existing trip parameters"]
        }
    
    print(f"[PARSER] Analyzing prompt: '{user_prompt}'")
    
    # Extract destination (common patterns)
    destination = state.get("destination", "Paris")  # default
    destination_patterns = [
        r"(?:to|visit|in)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:for|from|,|\$)",
        r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+trip",
        r"trip to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    ]
    
    for pattern in destination_patterns:
        match = re.search(pattern, user_prompt, re.IGNORECASE)
        if match:
            destination = match.group(1).strip()
            break
    
    # Extract budget (look for dollar amounts or numbers with "budget")
    budget = state.get("budget", 3000)  # default
    budget_patterns = [
        r"\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
        r"(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars|USD|usd)",
        r"budget\s+(?:of\s+)?\$?\s*(\d+(?:,\d{3})*)"
    ]
    
    for pattern in budget_patterns:
        match = re.search(pattern, user_prompt, re.IGNORECASE)
        if match:
            budget_str = match.group(1).replace(",", "")
            budget = float(budget_str)
            break
    
    # Extract origin (where traveling from)
    origin = state.get("origin", "New York")  # default
    origin_patterns = [
        r"from\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:to|for|,)",
        r"(?:leaving from|departing from|starting from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"
    ]
    
    for pattern in origin_patterns:
        match = re.search(pattern, user_prompt, re.IGNORECASE)
        if match:
            origin = match.group(1)
            break
    
    # Extract number of days
    num_days = state.get("num_days", 5)  # default
    days_patterns = [
        r"(\d+)\s*(?:days?|nights?)",
        r"for\s+(\d+)\s+(?:days?|nights?)",
        r"(\d+)[-\s]day"
    ]
    
    for pattern in days_patterns:
        match = re.search(pattern, user_prompt, re.IGNORECASE)
        if match:
            num_days = int(match.group(1))
            break
    
    # Ensure valid values
    if num_days <= 0:
        num_days = 1
    
    if budget <= 0:
        budget = 3000
    
    print(f"[PARSER] Extracted:")
    print(f"  Destination: {destination}")
    print(f"  Budget: ${budget:,.2f}")
    print(f"  Origin: {origin}")
    print(f"  Duration: {num_days} days")
    
    return {
        "destination": destination,
        "budget": budget,
        "origin": origin,
        "num_days": num_days,
        "messages": [f"Parser: Extracted trip to {destination} from {origin} for {num_days} days with ${budget:,.2f} budget"]
    }


# For future LLM-based implementation (using langchain)
def parse_prompt_with_llm(user_prompt: str):
    """
    Future implementation using LLM to parse complex natural language.
    
    Would use a prompt like:
    "Extract trip details from: '{user_prompt}'
     Return JSON with: destination, budget, origin, num_days, preferences"
    """
    # TODO: Implement with langchain LLM when API keys are available
    pass
