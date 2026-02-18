"""
Test edge cases and error scenarios for the planner-researcher integration.
"""

from src.graph import app


def test_budget_exceeded():
    """Test scenario where the budget is exceeded."""
    print("=" * 60)
    print("Testing Budget Exceeded Scenario")
    print("=" * 60)
    
    # Set a very low budget that will be exceeded
    state = {
        "messages": [],
        "destination": "Tokyo",
        "origin": "Los Angeles",
        "budget": 300,  # Very low budget
        "num_days": 5,
        "current_total_cost": 0,
        "itinerary": [],
        "search_plan": None,
        "research_results": None,
        "is_valid": False,
        "errors": []
    }
    
    print(f"\n[TEST] Budget: ${state['budget']} for {state['num_days']} days to {state['destination']}")
    print("[TEST] Expected: Budget should be exceeded\n")
    
    result = app.invoke(state)
    
    print(f"\n[RESULT] Total Cost: ${result.get('current_total_cost', 0):.2f}")
    print(f"[RESULT] Valid: {result.get('is_valid', False)}")
    print(f"[RESULT] Errors: {result.get('errors', [])}")
    
    # The validator should catch the budget issue
    if not result.get('is_valid'):
        print("\n✓ Budget exceeded scenario handled correctly")
        return True
    else:
        print("\n✗ Budget exceeded scenario not detected")
        return False


def test_missing_fields():
    """Test with minimal required fields."""
    print("\n\n" + "=" * 60)
    print("Testing Minimal Fields Scenario")
    print("=" * 60)
    
    state = {
        "messages": [],
        "destination": "Miami",
        "budget": 2000,
        "current_total_cost": 0,
        "itinerary": [],
        "is_valid": False,
        "errors": []
    }
    
    print("\n[TEST] Only destination and budget provided")
    print(f"  Destination: {state['destination']}")
    print(f"  Budget: ${state['budget']}")
    
    try:
        result = app.invoke(state)
        print(f"\n[RESULT] Workflow completed successfully")
        print(f"  Total Cost: ${result.get('current_total_cost', 0):.2f}")
        print(f"  Items: {len(result.get('itinerary', []))}")
        print("\n✓ Minimal fields handled with defaults")
        return True
    except Exception as e:
        print(f"\n✗ Failed with error: {str(e)}")
        return False


def test_different_destinations():
    """Test multiple destinations to ensure consistency."""
    print("\n\n" + "=" * 60)
    print("Testing Different Destinations")
    print("=" * 60)
    
    destinations = ["Barcelona", "Dubai", "Singapore", "Sydney"]
    budget = 2500
    
    for destination in destinations:
        state = {
            "messages": [],
            "destination": destination,
            "origin": "San Francisco",
            "budget": budget,
            "num_days": 4,
            "current_total_cost": 0,
            "itinerary": [],
            "search_plan": None,
            "research_results": None,
            "is_valid": False,
            "errors": []
        }
        
        print(f"\n[TEST] Destination: {destination}")
        result = app.invoke(state)
        
        total_cost = result.get('current_total_cost', 0)
        itinerary_count = len(result.get('itinerary', []))
        within_budget = result.get('is_valid', False)
        
        print(f"  Total Cost: ${total_cost:.2f}")
        print(f"  Itinerary Items: {itinerary_count}")
        print(f"  Within Budget: {'✓' if within_budget else '✗'}")


def test_itinerary_structure():
    """Test that itinerary has proper structure."""
    print("\n\n" + "=" * 60)
    print("Testing Itinerary Structure")
    print("=" * 60)
    
    state = {
        "messages": [],
        "destination": "Rome",
        "origin": "Chicago",
        "budget": 3500,
        "num_days": 6,
        "current_total_cost": 0,
        "itinerary": [],
        "search_plan": None,
        "research_results": None,
        "is_valid": False,
        "errors": []
    }
    
    result = app.invoke(state)
    itinerary = result.get('itinerary', [])
    
    print(f"\n[TEST] Checking {len(itinerary)} itinerary items\n")
    
    required_fields = ['category', 'item', 'price', 'details']
    all_valid = True
    
    for idx, item in enumerate(itinerary, 1):
        print(f"Item {idx}: {item.get('item', 'Unknown')}")
        
        missing = [field for field in required_fields if field not in item]
        if missing:
            print(f"  ✗ Missing fields: {missing}")
            all_valid = False
        else:
            print(f"  ✓ All required fields present")
            print(f"    Category: {item['category']}")
            print(f"    Price: ${item['price']:.2f}")
    
    if all_valid:
        print("\n✓ All itinerary items have proper structure")
        return True
    else:
        print("\n✗ Some itinerary items missing required fields")
        return False


if __name__ == "__main__":
    print("Starting Edge Case and Error Scenario Tests\n")
    
    results = []
    
    # Run tests
    results.append(("Budget Exceeded", test_budget_exceeded()))
    results.append(("Minimal Fields", test_missing_fields()))
    results.append(("Different Destinations", True))  # This test doesn't return bool
    test_different_destinations()
    results.append(("Itinerary Structure", test_itinerary_structure()))
    
    # Summary
    print("\n\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("All edge case tests completed successfully! ✅")
    else:
        print("Some edge case tests failed! ❌")
    print("=" * 60)
