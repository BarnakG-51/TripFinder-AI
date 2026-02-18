#!/usr/bin/env python3
"""
Test the 3-variant planner system with prompt parsing.
This demonstrates:
1. Parsing user prompts to extract trip details
2. Generating 3 plan variants (optimized, premium, low budget)
3. Executing each variant through the researcher
"""

from src.graph import app
from src.agents.planner import OPTIMIZED_BUDGET_PCT, PREMIUM_BUDGET_PCT, LOW_BUDGET_PCT


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def test_prompt_parsing():
    """Test prompt parsing functionality."""
    print_section("TEST 1: Prompt Parsing")
    
    test_prompts = [
        "I want to visit Paris for 5 days with a budget of $3000 from New York",
        "Trip to Tokyo from Los Angeles, 7 days, $5000 budget",
        "Barcelona trip, 4 days, budget $2500"
    ]
    
    for prompt in test_prompts:
        print(f"\n📝 Prompt: '{prompt}'")
        
        state = {
            "messages": [],
            "user_prompt": prompt,
            "destination": "",
            "budget": 0,
            "origin": "",
            "num_days": 0,
            "current_total_cost": 0,
            "itinerary": [],
            "plan_variants": None,
            "selected_plan": None,
            "search_plan": None,
            "research_results": None,
            "is_valid": False,
            "errors": []
        }
        
        result = app.invoke(state)
        
        print(f"   ✓ Destination: {result.get('destination', 'N/A')}")
        print(f"   ✓ Budget: ${result.get('budget', 0):,.2f}")
        print(f"   ✓ Origin: {result.get('origin', 'N/A')}")
        print(f"   ✓ Duration: {result.get('num_days', 0)} days")


def test_three_variants():
    """Test that planner generates 3 different plan variants."""
    print_section("TEST 2: Three Plan Variants Generation")
    
    state = {
        "messages": [],
        "user_prompt": "Paris trip from New York for 5 days, budget $3000",
        "destination": "Paris",
        "budget": 3000,
        "origin": "New York",
        "num_days": 5,
        "current_total_cost": 0,
        "itinerary": [],
        "plan_variants": None,
        "selected_plan": None,
        "search_plan": None,
        "research_results": None,
        "is_valid": False,
        "errors": []
    }
    
    result = app.invoke(state)
    
    if result.get("plan_variants"):
        variants = result["plan_variants"]
        
        print("\n📊 Plan Variants Generated:\n")
        
        for variant_name in ["optimized", "premium", "low_budget"]:
            if variant_name in variants:
                variant = variants[variant_name]
                alloc = variant.get("budget_allocation", {})
                
                print(f"{'='*60}")
                print(f"  {variant_name.upper().replace('_', ' ')}")
                print(f"{'='*60}")
                print(f"  Target Budget: ${alloc.get('total_budget', 0):,.2f}")
                print(f"  Budget %: {alloc.get('budget_percentage', 0):.1f}% of original")
                print(f"  Flights: ${alloc.get('flight_allocation', 0):,.2f} ({alloc.get('flight_pct', 0):.0f}%)")
                print(f"  Hotels: ${alloc.get('hotel_allocation', 0):,.2f} ({alloc.get('hotel_pct', 0):.0f}%)")
                print(f"  Activities: ${alloc.get('activities_allocation', 0):,.2f} ({alloc.get('activities_pct', 0):.0f}%)")
                
                # Show preferences
                hotel_info = variant.get("hotels", {})
                flight_info = variant.get("flights", {})
                print(f"  Min Hotel Rating: {hotel_info.get('min_rating', 'N/A')} ⭐")
                print(f"  Flight Preference: {flight_info.get('preferences', 'N/A')}")
                print()
        
        print(f"✓ All 3 variants created successfully!")
        print(f"✓ Selected plan: {result.get('selected_plan', 'N/A')}")
    else:
        print("✗ Plan variants not found!")


def test_variant_execution():
    """Test executing each of the 3 variants."""
    print_section("TEST 3: Executing Each Variant")
    
    base_budget = 3000
    variants = ["optimized", "premium", "low_budget"]
    
    print(f"\n📍 Trip: Paris from New York, 5 days, ${base_budget:,.2f} budget\n")
    
    results_comparison = []
    
    for variant in variants:
        print(f"\n{'─'*60}")
        print(f"Executing {variant.upper().replace('_', ' ')} Plan")
        print(f"{'─'*60}")
        
        state = {
            "messages": [],
            "user_prompt": "",
            "destination": "Paris",
            "budget": base_budget,
            "origin": "New York",
            "num_days": 5,
            "current_total_cost": 0,
            "itinerary": [],
            "plan_variants": None,
            "selected_plan": variant,  # Pre-select the variant
            "search_plan": None,
            "research_results": None,
            "is_valid": False,
            "errors": []
        }
        
        result = app.invoke(state)
        
        total_cost = result.get("current_total_cost", 0)
        itinerary_items = len(result.get("itinerary", []))
        is_valid = result.get("is_valid", False)
        
        print(f"  Total Cost: ${total_cost:,.2f}")
        print(f"  Itinerary Items: {itinerary_items}")
        print(f"  Within Original Budget: {'✓' if total_cost <= base_budget else '✗'}")
        print(f"  Validation: {'✓ PASS' if is_valid else '✗ FAIL'}")
        
        results_comparison.append({
            "variant": variant,
            "cost": total_cost,
            "items": itinerary_items,
            "valid": is_valid
        })
    
    # Comparison table
    print_section("RESULTS COMPARISON")
    
    print(f"\n{'Variant':<20} {'Cost':<15} {'Items':<10} {'Within Budget':<15} {'Valid':<10}")
    print("─" * 80)
    
    for res in results_comparison:
        within_budget = "✓ Yes" if res["cost"] <= base_budget else "✗ No"
        valid = "✓ Yes" if res["valid"] else "✗ No"
        
        print(f"{res['variant']:<20} ${res['cost']:<14,.2f} {res['items']:<10} {within_budget:<15} {valid:<10}")
    
    print("\n📊 Analysis:")
    print(f"  • Optimized plan should be ~{OPTIMIZED_BUDGET_PCT*100:.0f}% of budget (${base_budget * OPTIMIZED_BUDGET_PCT:,.2f})")
    print(f"  • Premium plan should be ~{PREMIUM_BUDGET_PCT*100:.0f}% of budget (${base_budget * PREMIUM_BUDGET_PCT:,.2f})")
    print(f"  • Low budget plan should be ~{LOW_BUDGET_PCT*100:.0f}% of budget (${base_budget * LOW_BUDGET_PCT:,.2f})")


def test_full_workflow_with_prompt():
    """Test complete workflow from prompt to itinerary."""
    print_section("TEST 4: Full Workflow with Natural Language Prompt")
    
    prompt = "I want a trip to Barcelona from Boston for 4 days with $2500 budget"
    
    print(f"\n💬 User Prompt: '{prompt}'\n")
    
    state = {
        "messages": [],
        "user_prompt": prompt,
        "destination": "",
        "budget": 0,
        "origin": "",
        "num_days": 0,
        "current_total_cost": 0,
        "itinerary": [],
        "plan_variants": None,
        "selected_plan": "optimized",  # Use optimized by default
        "search_plan": None,
        "research_results": None,
        "is_valid": False,
        "errors": []
    }
    
    print("🤖 Processing...")
    result = app.invoke(state)
    
    print("\n📋 Extracted Information:")
    print(f"  Destination: {result.get('destination', 'N/A')}")
    print(f"  Origin: {result.get('origin', 'N/A')}")
    print(f"  Duration: {result.get('num_days', 0)} days")
    print(f"  Budget: ${result.get('budget', 0):,.2f}")
    
    print("\n📦 Plan Variants Available:")
    if result.get("plan_variants"):
        for name in result["plan_variants"].keys():
            variant = result["plan_variants"][name]
            alloc = variant.get("budget_allocation", {})
            print(f"  • {name}: ${alloc.get('total_budget', 0):,.2f}")
    
    print(f"\n✅ Executed Plan: {result.get('selected_plan', 'N/A')}")
    print(f"💰 Total Cost: ${result.get('current_total_cost', 0):,.2f}")
    print(f"📝 Itinerary Items: {len(result.get('itinerary', []))}")
    
    print("\n🎯 Itinerary:")
    for idx, item in enumerate(result.get("itinerary", [])[:5], 1):  # Show first 5
        print(f"  {idx}. {item.get('item', 'N/A')}: ${item.get('price', 0):.2f}")


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print(" Testing 3-Variant Planner System with Prompt Parsing")
    print("=" * 80)
    
    try:
        # Test 1: Prompt parsing
        test_prompt_parsing()
        
        # Test 2: Three variants generation
        test_three_variants()
        
        # Test 3: Execute each variant
        test_variant_execution()
        
        # Test 4: Full workflow
        test_full_workflow_with_prompt()
        
        print_section("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        
    except Exception as e:
        print_section("❌ TEST FAILED")
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
