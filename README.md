# TripFinder-AI

An intelligent trip planning system that uses AI agents to search for flights, hotels, and travel spots within your budget.

## Overview

TripFinder-AI uses a multi-agent architecture built with LangGraph to plan and research travel itineraries:

1. **Planner Agent**: Creates a structured plan for searching hotels, flights, and travel spots
2. **Researcher Agent**: Executes the plan using search, maps, and finance tools
3. **Validator Agent**: Ensures the itinerary stays within budget

## Architecture

```
User Input → Planner → Researcher → Validator
                ↑          |            |
                |          |            |
                +----------+------------+
                     (if over budget)
```

### Agents

- **`src/agents/planner.py`**: Generates plans with tasks for the researcher
- **`src/agents/researcher.py`**: Uses tools to search for travel options and prices
- **`src/agents/validator.py`**: Validates the itinerary against the budget

### Tools

- **`src/tools/search.py`**: Web search using Tavily API for flights, hotels, and attractions
- **`src/tools/maps.py`**: Google Maps integration for distance calculations
- **`src/tools/finance.py`**: Budget tracking and cost calculations

### State Management

- **`src/state.py`**: Defines `AgentState` with plan, budget, itinerary, and validation fields
- **`src/graph.py`**: LangGraph workflow connecting all agents

## Installation

```bash
pip install -r requirements.txt
```

## Requirements

- Python 3.8+
- langchain-groq==1.1.2
- langgraph==1.0.8
- tavily-python
- googlemaps

## Configuration

Set the following environment variables for full functionality:

```bash
export TAVILY_API_KEY="your_tavily_api_key"
export GOOGLE_MAPS_API_KEY="your_google_maps_api_key"
```

> **Note**: The system works without API keys by using placeholder data for testing.

## Usage

### Running the Integration Test

```bash
python test_integration.py
```

This will test:
- Planner creating a structured plan
- Researcher executing the plan with tools
- Validator checking budget constraints

### Using the Graph

```python
from src.graph import app

# Initial state
initial_state = {
    "messages": [],
    "destination": "Paris",
    "budget": 2000.0,
    "current_total_cost": 0.0,
    "plan": None,
    "itinerary": [],
    "is_valid": False,
    "errors": []
}

# Run the workflow
result = app.invoke(initial_state)
print(f"Final cost: ${result['current_total_cost']}")
print(f"Within budget: {result['is_valid']}")
```

## Features

### Planner

The planner creates a structured plan with the following tasks:
1. Search for flights to the destination
2. Find hotels in the destination
3. Identify attractions and travel spots
4. Calculate distances between locations

### Researcher

The researcher executes each task using:
- **Search Tool**: Finds flights, hotels, and attractions using web search
- **Maps Tool**: Calculates distances and travel times
- **Finance Tool**: Tracks costs and validates against budget

### Validator

The validator checks if the total cost is within budget. If not, it sends the plan back to the planner for adjustments.

## Example Output

```
--- PLANNING ---
Plan created with 4 tasks for destination: Paris

--- RESEARCHING ---
Researching for destination: Paris, Budget: $2000.0
Executing task: Search for flights to Paris
  - Added flight to itinerary, cost: $500
Executing task: Find hotels in Paris
  - Added hotel to itinerary, cost: $400
Executing task: Identify travel spots and attractions in Paris
  - Added attractions to itinerary, cost: $300
Budget status: Within budget
Total cost: $1200.0, Budget: $2000.0

--- VALIDATING ---
✅ Trip is within budget!
```

## Testing

Run the integration test to verify the planner-researcher flow:

```bash
python test_integration.py
```

Tests include:
- Normal flow with sufficient budget
- Over-budget scenario triggering replanning
- Tool integration (with and without API keys)

## License

See LICENSE file for details.
