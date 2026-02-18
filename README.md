# TripFinder-AI Planner Tool

This project implements an AI-powered trip planning system that uses a planner-researcher architecture to find hotels, flights, and travel spots within a specified budget.

## Architecture

The system uses a graph-based workflow with three main nodes:

1. **Planner Node** (`src/agents/planner.py`)
   - Creates a structured search plan based on destination, budget, and trip duration
   - Allocates budget across flights (40%), hotels (35%), and activities (25%)
   - Generates specific search queries for the researcher

2. **Researcher Node** (`src/agents/researcher.py`)
   - Executes the search plan using specialized tools
   - Searches for flights, hotels, and travel spots
   - Calculates distances and total costs
   - Returns detailed itinerary with prices

3. **Validator Node** (`src/agents/validator.py`)
   - Validates the total cost against the budget
   - Returns errors if budget is exceeded
   - Triggers replanning if necessary

## Tools

The researcher uses three specialized tools:

### Search Tool (`src/tools/search.py`)
- `search_flights()` - Find flights between origin and destination
- `search_hotels()` - Find hotels at the destination
- `search_travel_spots()` - Find attractions and activities

### Maps Tool (`src/tools/maps.py`)
- `calculate_distance()` - Calculate distance between locations
- `get_route()` - Get route information with waypoints
- `get_nearby_places()` - Find nearby places of interest

### Finance Tool (`src/tools/finance.py`)
- `calculate_total_cost()` - Calculate total trip cost with breakdown
- `check_budget()` - Check if cost is within budget
- `estimate_daily_expenses()` - Estimate daily costs
- `calculate_price_per_person()` - Calculate per-person costs

## State Management

The `AgentState` (`src/state.py`) maintains:
- **User Input**: destination, origin, budget, num_days
- **Planning**: search_plan (queries for researcher)
- **Research**: research_results (prices, distances, options)
- **Output**: itinerary, current_total_cost
- **Validation**: is_valid, errors

## Workflow

```
User Input → Planner → Researcher → Validator → Output
                ↑                        |
                |_____(if invalid)_______|
```

1. User provides destination, origin, budget, and trip duration
2. Planner creates a structured search plan with budget allocation
3. Researcher executes searches using tools and builds itinerary
4. Validator checks if total cost is within budget
5. If invalid, returns to planner for adjustments
6. If valid, returns final itinerary

## Usage

```python
from src.graph import app

# Define initial state
state = {
    "messages": [],
    "destination": "Paris",
    "origin": "New York",
    "budget": 3000,
    "num_days": 5,
    "current_total_cost": 0,
    "itinerary": [],
    "search_plan": None,
    "research_results": None,
    "is_valid": False,
    "errors": []
}

# Run the workflow
result = app.invoke(state)

# Access results
print(f"Total Cost: ${result['current_total_cost']}")
print(f"Valid: {result['is_valid']}")
for item in result['itinerary']:
    print(f"- {item['item']}: ${item['price']}")
```

## Testing

Run the integration tests:

```bash
# Main integration test
python test_planner_integration.py

# Edge cases and error scenarios
python test_edge_cases.py
```

## Installation

```bash
pip install -r requirements.txt
```

## Dependencies

- `langchain-groq`: LLM integration
- `langgraph`: Graph-based workflow orchestration
- `tavily-python`: Web search capabilities (for future enhancement)

## Future Enhancements

1. **Real API Integration**: Replace simulated tools with real APIs
   - Google Flights API for flight search
   - Booking.com API for hotel search
   - Google Maps API for distance calculations
   - Currency conversion APIs

2. **LLM-Powered Planning**: Use LLMs for smarter planning
   - Natural language understanding of user preferences
   - Intelligent budget allocation based on destination
   - Personalized recommendations

3. **Enhanced Validation**: More sophisticated validation
   - Check travel dates and availability
   - Validate visa requirements
   - Check weather and seasonal factors

4. **User Preferences**: Support for user preferences
   - Hotel star rating preferences
   - Flight time preferences (morning/evening)
   - Activity type preferences (cultural, adventure, relaxation)
   - Dietary restrictions for restaurant recommendations

## Implementation Details

### Planner Tool Communication

The planner creates a `search_plan` dictionary that contains:
```python
{
    "flights": {
        "origin": str,
        "destination": str,
        "budget": float,
        "search_required": bool
    },
    "hotels": {
        "destination": str,
        "budget_per_night": float,
        "num_nights": int,
        "total_budget": float,
        "search_required": bool
    },
    "travel_spots": {
        "destination": str,
        "budget": float,
        "interests": list,
        "search_required": bool
    }
}
```

This structured plan is passed to the researcher through the state, ensuring clear communication between agents.

### Researcher Tool Usage

The researcher executes the plan in order:
1. Searches for flights using the search tool
2. Calculates distance using the maps tool
3. Searches for hotels at destination
4. Searches for travel spots and activities
5. Calculates total cost using the finance tool
6. Checks budget status

All results are stored in `research_results` and the selected options are added to the `itinerary`.
