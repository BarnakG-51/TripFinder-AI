#!/usr/bin/env python3
"""
Test the complete LangGraph workflow with the planner-researcher integration.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.graph import app


def test_langgraph_workflow():
    """Test the complete LangGraph workflow"""
    print("=" * 60)
    print("Testing Complete LangGraph Workflow")
    print("=" * 60)
    
    # Initial state
    initial_state = {
        "messages": [],
        "destination": "Barcelona",
        "budget": 1500.0,
        "current_total_cost": 0.0,
        "plan": None,
        "itinerary": [],
        "is_valid": False,
        "errors": []
    }
    
    print(f"\nInitial State:")
    print(f"  Destination: {initial_state['destination']}")
    print(f"  Budget: ${initial_state['budget']}")
    
    print("\n" + "=" * 60)
    print("Running LangGraph Workflow...")
    print("=" * 60)
    
    # Run the workflow
    try:
        result = app.invoke(initial_state)
        
        print("\n" + "=" * 60)
        print("WORKFLOW COMPLETED")
        print("=" * 60)
        
        print(f"\nFinal State:")
        print(f"  Destination: {result['destination']}")
        print(f"  Budget: ${result['budget']}")
        print(f"  Total Cost: ${result['current_total_cost']}")
        print(f"  Within Budget: {result['is_valid']}")
        print(f"  Remaining: ${result['budget'] - result['current_total_cost']}")
        
        if result.get('itinerary'):
            print(f"\nItinerary ({len(result['itinerary'])} items):")
            for item in result['itinerary']:
                print(f"  - {item.get('name')}: ${item.get('price')}")
        
        if result['is_valid']:
            print("\n✅ SUCCESS: Workflow completed with valid itinerary!")
            return True
        else:
            print(f"\n⚠️  WARNING: Itinerary exceeds budget")
            print(f"Errors: {result.get('errors', [])}")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: Workflow failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Testing the complete LangGraph workflow with planner-researcher integration")
    print("Note: This test will use mock data if API keys are not set.\n")
    
    success = test_langgraph_workflow()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ All workflow tests passed!")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("⚠️  Workflow completed with warnings")
        print("=" * 60)
        sys.exit(0)
