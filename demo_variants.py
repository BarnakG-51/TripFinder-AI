#!/usr/bin/env python3
"""
Demo for 3-variant planner system with prompt parsing.
Shows how the system generates and executes optimized, premium, and low-budget plans.
"""

from src.graph import app


def print_section(title, width=80):
    """Print a formatted section header."""
    print("\n" + "=" * width)
    print(f" {title}")
    print("=" * width)


def demo_three_variants_comparison():
    """Demo showing all 3 plan variants side by side."""
    print_section("TripFinder-AI: 3-Variant Planner System")
    
    user_prompt = "I want to visit Paris from New York for 5 days with a budget of $3000"
    
    print(f"\n💬 User Input:")
    print(f'   "{user_prompt}"')
    
    print("\n🤖 System Processing:")
    print("   1. Parsing prompt to extract trip details...")
    print("   2. Generating 3 plan variants (Optimized, Premium, Low Budget)...")
    print("   3. Executing each variant through researcher...")
    
    # Store results for each variant
    all_results = {}
    
    for variant_name in ["optimized", "premium", "low_budget"]:
        state = {
            "messages": [],
            "user_prompt": user_prompt,
            "destination": "",
            "budget": 0,
            "origin": "",
            "num_days": 0,
            "current_total_cost": 0,
            "itinerary": [],
            "plan_variants": None,
            "selected_plan": variant_name,
            "search_plan": None,
            "research_results": None,
            "is_valid": False,
            "errors": []
        }
        
        result = app.invoke(state)
        all_results[variant_name] = result
    
    # Get one result for parsed info (all should be the same)
    sample = all_results["optimized"]
    
    print_section("📝 Parsed Trip Details")
    print(f"\n   Destination: {sample.get('destination')}")
    print(f"   Origin: {sample.get('origin')}")
    print(f"   Duration: {sample.get('num_days')} days")
    print(f"   Budget: ${sample.get('budget'):,.2f}")
    
    print_section("📊 Three Plan Variants Comparison")
    
    # Get plan variants from one result
    plan_variants = sample.get("plan_variants", {})
    
    variant_display = {
        "optimized": "💎 OPTIMIZED PLAN",
        "premium": "⭐ PREMIUM EXPERIENCE", 
        "low_budget": "💰 LOW BUDGET PLAN"
    }
    
    for variant_name in ["optimized", "premium", "low_budget"]:
        result = all_results[variant_name]
        variant_plan = plan_variants.get(variant_name, {})
        alloc = variant_plan.get("budget_allocation", {})
        
        print(f"\n{variant_display[variant_name]}")
        print("─" * 60)
        
        # Plan details
        print(f"Target Budget: ${alloc.get('total_budget', 0):,.2f}")
        print(f"Budget Percentage: {alloc.get('budget_percentage', 0):.0f}% of original")
        print(f"\nBudget Allocation:")
        print(f"  • Flights: ${alloc.get('flight_allocation', 0):,.2f} ({alloc.get('flight_pct', 0):.0f}%)")
        print(f"  • Hotels: ${alloc.get('hotel_allocation', 0):,.2f} ({alloc.get('hotel_pct', 0):.0f}%)")
        print(f"  • Activities: ${alloc.get('activities_allocation', 0):,.2f} ({alloc.get('activities_pct', 0):.0f}%)")
        
        # Preferences
        hotel_info = variant_plan.get("hotels", {})
        flight_info = variant_plan.get("flights", {})
        print(f"\nPreferences:")
        print(f"  • Min Hotel Rating: {hotel_info.get('min_rating', 'N/A')} ⭐")
        print(f"  • Flight Preference: {flight_info.get('preferences', 'N/A')}")
        
        # Actual results
        total_cost = result.get("current_total_cost", 0)
        itinerary = result.get("itinerary", [])
        
        print(f"\nActual Results:")
        print(f"  • Total Cost: ${total_cost:,.2f}")
        print(f"  • Items in Itinerary: {len(itinerary)}")
        print(f"  • Within Original Budget: {'✓ Yes' if total_cost <= sample.get('budget', 0) else '✗ No'}")
        print(f"  • Validation: {'✓ Valid' if result.get('is_valid') else '✗ Invalid'}")
    
    print_section("🎯 Detailed Itineraries")
    
    for variant_name in ["optimized", "premium", "low_budget"]:
        result = all_results[variant_name]
        itinerary = result.get("itinerary", [])
        
        print(f"\n{variant_display[variant_name]}")
        print("─" * 60)
        
        for idx, item in enumerate(itinerary, 1):
            category_emoji = {
                "flights": "✈️",
                "hotels": "🏨",
                "activities": "🎯"
            }.get(item["category"], "📌")
            
            print(f"{idx}. {category_emoji} {item['item']}: ${item['price']:,.2f}")
        
        total = result.get("current_total_cost", 0)
        print(f"\n   Total: ${total:,.2f}")
    
    print_section("📈 Summary & Recommendations")
    
    optimized_result = all_results["optimized"]
    premium_result = all_results["premium"]
    low_result = all_results["low_budget"]
    
    base_budget = sample.get("budget", 0)
    
    print(f"\n💰 Budget: ${base_budget:,.2f}")
    print(f"\n✓ Optimized Plan (${optimized_result.get('current_total_cost', 0):,.2f}):")
    print(f"  Best balance of cost and quality. Stays within budget")
    print(f"  with ${base_budget - optimized_result.get('current_total_cost', 0):,.2f} to spare.")
    
    premium_cost = premium_result.get("current_total_cost", 0)
    over_amount = premium_cost - base_budget
    print(f"\n⭐ Premium Plan (${premium_cost:,.2f}):")
    if over_amount > 0:
        print(f"  Best amenities and experiences. ${over_amount:,.2f} over budget.")
        print(f"  Consider if you can extend your budget.")
    else:
        print(f"  Best amenities and experiences within budget!")
    
    low_cost = low_result.get("current_total_cost", 0)
    savings = base_budget - low_cost
    print(f"\n💰 Low Budget Plan (${low_cost:,.2f}):")
    print(f"  Economical option. Saves ${savings:,.2f} ({savings/base_budget*100:.0f}%)")
    print(f"  Perfect if you want to minimize costs.")
    
    print("\n" + "=" * 80)


def demo_different_prompts():
    """Demo with different natural language prompts."""
    print_section("Testing Different Natural Language Prompts")
    
    prompts = [
        "Tokyo trip from Los Angeles, 7 days, $5000 budget",
        "I want to visit Barcelona for 4 days with $2500 budget",
        "Trip to London from Boston for 6 days, budget $4000"
    ]
    
    for prompt in prompts:
        print(f"\n{'─'*60}")
        print(f"💬 Prompt: \"{prompt}\"")
        print(f"{'─'*60}")
        
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
            "selected_plan": "optimized",
            "search_plan": None,
            "research_results": None,
            "is_valid": False,
            "errors": []
        }
        
        result = app.invoke(state)
        
        print(f"\n✓ Parsed: {result.get('origin')} → {result.get('destination')}")
        print(f"  Duration: {result.get('num_days')} days | Budget: ${result.get('budget'):,.2f}")
        
        if result.get("plan_variants"):
            print(f"\n  3 Variants Generated:")
            for name, variant in result["plan_variants"].items():
                budget = variant["budget_allocation"]["total_budget"]
                pct = variant["budget_allocation"]["budget_percentage"]
                print(f"    • {name}: ${budget:,.2f} ({pct:.0f}% of original)")


def main():
    """Run demos."""
    print("\n" + "=" * 80)
    print(" TripFinder-AI Demo: 3-Variant Planner with Prompt Parsing")
    print("=" * 80)
    print("\n This demo showcases:")
    print("  • Natural language prompt parsing")
    print("  • Automatic generation of 3 plan variants")
    print("  • Side-by-side comparison of Optimized, Premium, and Low Budget plans")
    print("=" * 80)
    
    # Main demo
    demo_three_variants_comparison()
    
    # Additional prompt examples
    demo_different_prompts()
    
    print("\n" + "=" * 80)
    print(" Demo Complete!")
    print(" The system successfully:")
    print("  ✓ Parsed natural language prompts")
    print("  ✓ Generated 3 distinct plan variants")
    print("  ✓ Executed research for each variant")
    print("  ✓ Provided detailed itineraries for all options")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
