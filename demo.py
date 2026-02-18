#!/usr/bin/env python3
"""
Demo script showing how to use the TripFinder-AI planner tool.
This demonstrates the complete workflow from planning to final itinerary.
"""

from src.graph import app
import json


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def demo_basic_trip():
    """Demo a basic trip planning scenario."""
    print_section("DEMO: Planning a Trip to Paris")
    
    # User input
    trip_request = {
        "destination": "Paris",
        "origin": "New York",
        "budget": 3000,
        "num_days": 5
    }
    
    print("\n📝 Trip Request:")
    print(f"   From: {trip_request['origin']}")
    print(f"   To: {trip_request['destination']}")
    print(f"   Budget: ${trip_request['budget']:,.2f}")
    print(f"   Duration: {trip_request['num_days']} days")
    
    # Create initial state
    state = {
        "messages": [],
        "destination": trip_request["destination"],
        "origin": trip_request["origin"],
        "budget": trip_request["budget"],
        "num_days": trip_request["num_days"],
        "current_total_cost": 0,
        "itinerary": [],
        "search_plan": None,
        "research_results": None,
        "is_valid": False,
        "errors": []
    }
    
    print("\n🤖 Running AI Trip Planner...")
    print("   → Planner creating search plan...")
    print("   → Researcher finding options...")
    print("   → Validator checking budget...")
    
    # Run the workflow
    result = app.invoke(state)
    
    # Display results
    print_section("RESULTS")
    
    # Budget allocation
    if result.get("search_plan") and "budget_allocation" in result["search_plan"]:
        alloc = result["search_plan"]["budget_allocation"]
        print("\n💰 Budget Allocation:")
        print(f"   Total Budget: ${alloc['total_budget']:,.2f}")
        print(f"   Flights: ${alloc['flight_allocation']:,.2f} (40%)")
        print(f"   Hotels: ${alloc['hotel_allocation']:,.2f} (35%)")
        print(f"   Activities: ${alloc['activities_allocation']:,.2f} (25%)")
    
    # Itinerary
    print("\n✈️ Your Itinerary:")
    if result.get("itinerary"):
        for idx, item in enumerate(result["itinerary"], 1):
            category_emoji = {
                "flights": "✈️",
                "hotels": "🏨",
                "activities": "🎯"
            }.get(item["category"], "📌")
            print(f"\n   {idx}. {category_emoji} {item['item']}")
            print(f"      Price: ${item['price']:,.2f}")
            
            # Show some details
            details = item.get("details", {})
            if item["category"] == "flights":
                print(f"      Duration: {details.get('duration', 'N/A')}")
                print(f"      Stops: {details.get('stops', 'N/A')}")
            elif item["category"] == "hotels":
                print(f"      Rating: {details.get('rating', 'N/A')} ⭐")
                print(f"      Nights: {details.get('num_nights', 'N/A')}")
            elif item["category"] == "activities":
                print(f"      Category: {details.get('category', 'N/A').title()}")
                print(f"      Time needed: {details.get('estimated_time', 'N/A')}")
    
    # Cost summary
    print("\n💵 Cost Summary:")
    print(f"   Total Cost: ${result.get('current_total_cost', 0):,.2f}")
    print(f"   Budget: ${trip_request['budget']:,.2f}")
    remaining = trip_request['budget'] - result.get('current_total_cost', 0)
    print(f"   Remaining: ${remaining:,.2f}")
    
    # Validation
    print("\n✅ Validation:")
    if result.get('is_valid'):
        print("   Status: ✓ Trip is within budget!")
    else:
        print("   Status: ✗ Budget exceeded")
        if result.get('errors'):
            for error in result['errors']:
                print(f"   Error: {error}")
    
    # Distance info
    if result.get("research_results") and "distances" in result["research_results"]:
        dist = result["research_results"]["distances"].get("flight_route", {})
        if dist:
            print("\n📏 Travel Distance:")
            print(f"   {dist.get('distance_km', 0)} km ({dist.get('distance_miles', 0)} miles)")
    
    return result


def demo_budget_comparison():
    """Demo comparing different budget scenarios."""
    print_section("DEMO: Budget Comparison for Barcelona Trip")
    
    budgets = [
        ("Low Budget", 1500),
        ("Medium Budget", 2500),
        ("High Budget", 4000)
    ]
    
    print("\n📊 Comparing different budget levels for a 4-day trip to Barcelona:\n")
    
    results = []
    for name, budget in budgets:
        state = {
            "messages": [],
            "destination": "Barcelona",
            "origin": "Boston",
            "budget": budget,
            "num_days": 4,
            "current_total_cost": 0,
            "itinerary": [],
            "search_plan": None,
            "research_results": None,
            "is_valid": False,
            "errors": []
        }
        
        result = app.invoke(state)
        results.append((name, budget, result))
    
    # Display comparison
    print(f"{'Budget Level':<20} {'Budget':<15} {'Total Cost':<15} {'Items':<10} {'Status':<10}")
    print("-" * 70)
    
    for name, budget, result in results:
        total_cost = result.get('current_total_cost', 0)
        num_items = len(result.get('itinerary', []))
        status = "✓ OK" if result.get('is_valid') else "✗ Over"
        
        print(f"{name:<20} ${budget:<14,.2f} ${total_cost:<14,.2f} {num_items:<10} {status:<10}")


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print(" TripFinder-AI Demo - Planner Tool with Multi-Tool Integration")
    print("=" * 70)
    
    # Demo 1: Basic trip
    demo_basic_trip()
    
    # Demo 2: Budget comparison
    demo_budget_comparison()
    
    print_section("Demo Complete!")
    print("\n✨ The planner tool successfully:")
    print("   • Created structured search plans")
    print("   • Used search tool to find flights, hotels, and activities")
    print("   • Used maps tool to calculate distances")
    print("   • Used finance tool to track costs and validate budget")
    print("   • Generated complete itineraries within budget")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
