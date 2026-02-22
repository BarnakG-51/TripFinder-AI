"""
Test script to validate the planner-researcher integration.
This script tests the complete workflow from planning to research.
"""

from src.graph import app
from src.state import AgentState
from typing import Dict, Any


def test_planner_researcher_workflow():
    """Test the complete planner -> researcher -> validator workflow."""
    print("=" * 60)
    print("Testing Planner-Researcher Integration")
    print("=" * 60)
    
    # Create initial state
    initial_state = {
        "messages": [],
        "destination": "Paris",
        "origin": "New York",
        "budget": 4000,
        "num_days": 5,
        "current_total_cost": 0,
        "itinerary": [],
        "search_plan": None,
        "research_results": None,
        "is_valid": False,
        "errors": []
    }
    
    print("\n[TEST] Initial State:")
    print(f"  Destination: {initial_state['destination']}")
    print(f"  Origin: {initial_state['origin']}")
    print(f"  Budget: ${initial_state['budget']}")
    print(f"  Duration: {initial_state['num_days']} days")
    
    # Run the workflow
    print("\n[TEST] Running workflow...\n")
    try:
        result = app.invoke(initial_state)
        
        print("\n" + "=" * 60)
        print("Workflow Results")
        print("=" * 60)
        
        # Display search plan
        if "search_plan" in result and result["search_plan"]:
            print("\n[SEARCH PLAN]")
            plan = result["search_plan"]
            if "budget_allocation" in plan:
                alloc = plan["budget_allocation"]
                print(f"  Total Budget: ${alloc.get('total_budget', 0):.2f}")
                print(f"  Flight Budget: ${alloc.get('flight_allocation', 0):.2f}")
                print(f"  Hotel Budget: ${alloc.get('hotel_allocation', 0):.2f}")
                print(f"  Activities Budget: ${alloc.get('activities_allocation', 0):.2f}")
        
        # Display research results summary
        if "research_results" in result and result["research_results"]:
            print("\n[RESEARCH RESULTS]")
            research = result["research_results"]
            print(f"  Flights found: {len(research.get('flights', []))}")
            print(f"  Hotels found: {len(research.get('hotels', []))}")
            print(f"  Travel spots found: {len(research.get('travel_spots', []))}")
            
            if "distances" in research and "flight_route" in research["distances"]:
                dist = research["distances"]["flight_route"]
                print(f"  Distance: {dist.get('distance_km', 0)} km ({dist.get('distance_miles', 0)} miles)")
        
        # Display itinerary
        if "itinerary" in result and result["itinerary"]:
            print("\n[ITINERARY]")
            for item in result["itinerary"]:
                print(f"  - {item['item']}: ${item['price']:.2f}")
        
        # Display cost summary
        print("\n[COST SUMMARY]")
        print(f"  Total Cost: ${result.get('current_total_cost', 0):.2f}")
        print(f"  Budget: ${initial_state['budget']:.2f}")
        print(f"  Remaining: ${initial_state['budget'] - result.get('current_total_cost', 0):.2f}")
        
        # Display validation status
        print("\n[VALIDATION]")
        print(f"  Valid: {result.get('is_valid', False)}")
        if result.get('errors'):
            print(f"  Errors: {', '.join(result['errors'])}")
        else:
            print("  No errors")
        
        # Test assertions
        print("\n" + "=" * 60)
        print("Test Assertions")
        print("=" * 60)
        
        assert "search_plan" in result, "Search plan should be created"
        print("✓ Search plan created")
        
        assert "research_results" in result, "Research results should be returned"
        print("✓ Research results returned")
        
        assert "itinerary" in result and len(result["itinerary"]) > 0, "Itinerary should have items"
        print(f"✓ Itinerary has {len(result['itinerary'])} items")
        
        assert "current_total_cost" in result and result["current_total_cost"] > 0, "Total cost should be calculated"
        print(f"✓ Total cost calculated: ${result['current_total_cost']:.2f}")
        
        assert "is_valid" in result, "Validation status should be present"
        print(f"✓ Validation completed: {'PASS' if result['is_valid'] else 'FAIL'}")
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_budget_scenarios():
    """Test different budget scenarios."""
    print("\n\n" + "=" * 60)
    print("Testing Budget Scenarios")
    print("=" * 60)
    
    scenarios = [
        {"name": "Low Budget", "budget": 1500, "num_days": 3},
        {"name": "Medium Budget", "budget": 3000, "num_days": 5},
        {"name": "High Budget", "budget": 5000, "num_days": 7},
    ]
    
    for scenario in scenarios:
        print(f"\n[SCENARIO] {scenario['name']} - Budget: ${scenario['budget']}, Days: {scenario['num_days']}")
        
        state = {
            "messages": [],
            "destination": "London",
            "origin": "Boston",
            "budget": scenario["budget"],
            "num_days": scenario["num_days"],
            "current_total_cost": 0,
            "itinerary": [],
            "search_plan": None,
            "research_results": None,
            "is_valid": False,
            "errors": []
        }
        
        try:
            result = app.invoke(state)
            total_cost = result.get("current_total_cost", 0)
            within_budget = result.get("is_valid", False)
            
            print(f"  Total Cost: ${total_cost:.2f}")
            print(f"  Within Budget: {'✓' if within_budget else '✗'}")
            print(f"  Items in Itinerary: {len(result.get('itinerary', []))}")
            
        except Exception as e:
            print(f"  Error: {str(e)}")


if __name__ == "__main__":
    print("Starting Planner-Researcher Integration Tests\n")
    
    # Run main workflow test
    success = test_planner_researcher_workflow()
    
    # Run budget scenarios test
    test_budget_scenarios()
    
    print("\n" + "=" * 60)
    if success:
        print("Test suite completed successfully! ✅")
    else:
        print("Test suite failed! ❌")
    print("=" * 60)
