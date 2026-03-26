# TripFinder-AI Planner Tool

This project implements an AI-powered trip planning system with **3-variant plan generation** (Optimized, Premium, Low Budget) that uses a planner-researcher architecture to find hotels, flights, and travel spots.

The website is live at https://tripfinder-ai.streamlit.app/

## Key Features

- 🤖 **Natural Language Processing**: Parse user prompts to extract trip details
- 📊 **3-Variant Planning**: Automatically generate Optimized, Premium, and Low Budget plans
- 🔍 **Multi-Tool Research**: Search for flights, hotels, and activities using specialized tools
- 💰 **Smart Budget Allocation**: Different allocation strategies per variant
- 📏 **Distance Calculation**: Calculate travel distances and routes
- ✅ **Automatic Validation**: Ensure plans stay within budget constraints

## Architecture

The system uses a graph-based workflow with four main nodes:

0. **Prompt Parser Node** (`src/agents/prompt_parser.py`) - NEW!
   - Parses natural language user prompts
   - Extracts destination, origin, budget, and trip duration
   - Uses pattern matching (future: LLM-based parsing)

1. **Planner Node** (`src/agents/planner.py`) - ENHANCED!
   - **Generates 3 distinct plan variants**:
     - **Optimized Plan**: 96% of budget, balanced allocation (40/35/25)
     - **Premium Experience**: 115% of budget, quality focus (35/40/25, min 4.5★ hotels, direct flights)
     - **Low Budget Plan**: 50% of budget, cost-optimized (45/30/25, min 3.0★ hotels)
   - Each variant has custom budget allocation and preferences
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

## 3-Variant System

### Variant Comparison

| Variant | Budget Target | Flight % | Hotel % | Activities % | Hotel Rating | Flight Pref |
|---------|--------------|----------|---------|--------------|--------------|-------------|
| **Optimized** | 96% | 40% | 35% | 25% | 3.5★ | Cheapest |
| **Premium** | 115% | 35% | 40% | 25% | 4.5★ | Direct |
| **Low Budget** | 50% | 45% | 30% | 25% | 3.0★ | Cheapest |

### How It Works

1. User provides a natural language prompt (e.g., "Paris trip from New York for 5 days, $3000 budget")
2. Prompt parser extracts structured information
3. Planner generates all 3 variants simultaneously
4. Selected variant (default: optimized) is executed by researcher
5. All 3 variants available for comparison in results

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
- **User Input**: user_prompt, destination, origin, budget, num_days
- **Planning**: plan_variants (all 3 variants), selected_plan, search_plan (active variant)
- **Research**: research_results (prices, distances, options)
- **Output**: itinerary, current_total_cost
- **Validation**: is_valid, errors

## Workflow

```
User Prompt → Parser → Planner (3 variants) → Researcher → Validator → Output
                           ↑                                    |
                           |____________(if invalid)____________|
```

1. User provides a natural language prompt
2. Parser extracts destination, origin, budget, and trip duration
3. Planner generates 3 plan variants (Optimized, Premium, Low Budget)
4. Researcher executes the selected variant using tools and builds itinerary
5. Validator checks if total cost is within budget
5. If invalid, returns to planner for adjustments
6. If valid, returns final itinerary

## Usage

### Option 1: Natural Language Prompt (Recommended)

```python
from src.graph import app

# Use natural language prompt
state = {
    "messages": [],
    "user_prompt": "I want to visit Paris from New York for 5 days with $3000 budget",
    "destination": "",
    "origin": "",
    "budget": 0,
    "num_days": 0,
    "current_total_cost": 0,
    "itinerary": [],
    "plan_variants": None,
    "selected_plan": "optimized",  # "optimized", "premium", or "low_budget"
    "search_plan": None,
    "research_results": None,
    "is_valid": False,
    "errors": []
}

# Run the workflow
result = app.invoke(state)

# Access all 3 plan variants
for variant_name, variant_plan in result["plan_variants"].items():
    budget = variant_plan["budget_allocation"]["total_budget"]
    print(f"{variant_name}: ${budget:.2f}")

# Access executed variant results
print(f"Selected: {result['selected_plan']}")
print(f"Total Cost: ${result['current_total_cost']}")
print(f"Valid: {result['is_valid']}")
for item in result['itinerary']:
    print(f"- {item['item']}: ${item['price']}")
```

### Option 2: Direct Parameters

```python
from src.graph import app

# Provide parameters directly
state = {
    "messages": [],
    "user_prompt": "",  # Empty when using direct parameters
    "destination": "Paris",
    "origin": "New York",
    "budget": 3000,
    "num_days": 5,
    "current_total_cost": 0,
    "itinerary": [],
    "plan_variants": None,
    "selected_plan": "optimized",
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
# Original integration test
python test_planner_integration.py

# Edge cases and error scenarios
python test_edge_cases.py

# 3-variant system test (NEW!)
python test_three_variants.py
```

## Demos

```bash
# Original demo (single plan)
python demo.py

# 3-variant comparison demo (NEW!)
python demo_variants.py
```

The variant demo shows:
- Natural language prompt parsing
- Side-by-side comparison of all 3 variants
- Detailed budget allocations and preferences
- Complete itineraries for each variant

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
