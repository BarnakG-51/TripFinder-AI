#!/usr/bin/env python3
"""
Test script to verify planner-researcher integration.
Tests the flow: planner creates plan -> researcher uses tools -> validator checks budget
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.state import AgentState
from src.agents.planner import planner_node
from src.agents.researcher import researcher_node
from src.agents.validator import validator_node


def test_planner_researcher_flow():
    """Test the complete flow from planner to researcher to validator"""
    print("=" * 60)
    print("Testing Planner-Researcher Integration")
    print("=" * 60)
    
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
    
    print("\n1. Testing Planner Node")
    print("-" * 60)
    planner_result = planner_node(initial_state)
    print(f"Planner output keys: {planner_result.keys()}")
    print(f"Plan created: {planner_result.get('plan') is not None}")
    
    if planner_result.get('plan'):
        plan = planner_result['plan']
        print(f"Plan destination: {plan.get('destination')}")
        print(f"Plan budget: ${plan.get('budget')}")
        print(f"Number of tasks: {len(plan.get('tasks', []))}")
        for i, task in enumerate(plan.get('tasks', []), 1):
            print(f"  Task {i}: {task.get('task_type')} - {task.get('description')}")
    
    # Update state with planner results
    state_after_planner = {**initial_state, **planner_result}
    
    print("\n2. Testing Researcher Node")
    print("-" * 60)
    researcher_result = researcher_node(state_after_planner)
    print(f"Researcher output keys: {researcher_result.keys()}")
    print(f"Total cost: ${researcher_result.get('current_total_cost', 0)}")
    print(f"Number of itinerary items: {len(researcher_result.get('itinerary', []))}")
    
    if researcher_result.get('itinerary'):
        print("\nItinerary breakdown:")
        for item in researcher_result['itinerary']:
            print(f"  - {item.get('name')}: ${item.get('price')} - {item.get('description')}")
    
    # Update state with researcher results
    state_after_researcher = {**state_after_planner, **researcher_result}
    
    print("\n3. Testing Validator Node")
    print("-" * 60)
    validator_result = validator_node(state_after_researcher)
    print(f"Validator output keys: {validator_result.keys()}")
    print(f"Is valid: {validator_result.get('is_valid')}")
    print(f"Errors: {validator_result.get('errors', [])}")
    
    # Final state
    final_state = {**state_after_researcher, **validator_result}
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Destination: {final_state['destination']}")
    print(f"Budget: ${final_state['budget']}")
    print(f"Total Cost: ${final_state['current_total_cost']}")
    print(f"Within Budget: {final_state['is_valid']}")
    print(f"Remaining: ${final_state['budget'] - final_state['current_total_cost']}")
    
    if final_state['is_valid']:
        print("\n✅ TEST PASSED: Trip is within budget!")
    else:
        print("\n❌ TEST FAILED: Trip exceeds budget!")
        print(f"Errors: {final_state['errors']}")
    
    return final_state


def test_over_budget_scenario():
    """Test scenario where the budget is exceeded"""
    print("\n\n" + "=" * 60)
    print("Testing Over-Budget Scenario")
    print("=" * 60)
    
    # Initial state with low budget
    initial_state = {
        "messages": [],
        "destination": "Tokyo",
        "budget": 500.0,  # Low budget that will be exceeded
        "current_total_cost": 0.0,
        "plan": None,
        "itinerary": [],
        "is_valid": False,
        "errors": []
    }
    
    # Run through the flow
    planner_result = planner_node(initial_state)
    state_after_planner = {**initial_state, **planner_result}
    
    researcher_result = researcher_node(state_after_planner)
    state_after_researcher = {**state_after_planner, **researcher_result}
    
    validator_result = validator_node(state_after_researcher)
    final_state = {**state_after_researcher, **validator_result}
    
    print(f"\nBudget: ${final_state['budget']}")
    print(f"Total Cost: ${final_state['current_total_cost']}")
    print(f"Is valid: {final_state['is_valid']}")
    
    if not final_state['is_valid']:
        print("\n✅ TEST PASSED: Budget validation correctly detected overspending!")
    else:
        print("\n❌ TEST FAILED: Budget validation should have detected overspending!")
    
    return final_state


if __name__ == "__main__":
    print("Note: This test will use mock data if API keys are not set.")
    print("Set TAVILY_API_KEY and GOOGLE_MAPS_API_KEY for full testing.\n")
    
    try:
        # Test 1: Normal flow
        test_planner_researcher_flow()
        
        # Test 2: Over-budget scenario
        test_over_budget_scenario()
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
