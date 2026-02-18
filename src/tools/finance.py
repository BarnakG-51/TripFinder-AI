"""
Finance tool for budget tracking and price calculations.
This tool handles all financial calculations for the trip.
"""

from typing import Dict, Any, List


def calculate_total_cost(itinerary_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate total cost from all itinerary items.
    
    Args:
        itinerary_items: List of items with price information
    
    Returns:
        Dictionary with cost breakdown
    """
    total = 0
    breakdown = {
        "flights": 0,
        "hotels": 0,
        "activities": 0,
        "meals": 0,
        "other": 0
    }
    
    for item in itinerary_items:
        price = item.get("price", 0)
        category = item.get("category", "other").lower()
        
        total += price
        
        if category in breakdown:
            breakdown[category] += price
        else:
            breakdown["other"] += price
    
    result = {
        "total_cost": round(total, 2),
        "breakdown": breakdown,
        "currency": "USD"
    }
    
    print(f"[FINANCE] Total cost calculated: ${total:.2f}")
    return result


def check_budget(current_cost: float, budget: float) -> Dict[str, Any]:
    """
    Check if current cost is within budget.
    
    Args:
        current_cost: Current total cost
        budget: Maximum budget
    
    Returns:
        Dictionary with budget status
    """
    remaining = budget - current_cost
    percentage_used = (current_cost / budget * 100) if budget > 0 else 0
    
    result = {
        "budget": budget,
        "current_cost": current_cost,
        "remaining": remaining,
        "percentage_used": round(percentage_used, 2),
        "within_budget": current_cost <= budget,
        "status": "OK" if current_cost <= budget else "OVER_BUDGET"
    }
    
    if result["within_budget"]:
        print(f"[FINANCE] Budget OK: ${current_cost:.2f} / ${budget:.2f} ({percentage_used:.1f}% used)")
    else:
        print(f"[FINANCE] Budget EXCEEDED: ${current_cost:.2f} / ${budget:.2f} (Over by ${-remaining:.2f})")
    
    return result


def estimate_daily_expenses(destination: str, num_days: int, comfort_level: str = "moderate") -> Dict[str, Any]:
    """
    Estimate daily expenses for a destination.
    
    Args:
        destination: Travel destination
        num_days: Number of days
        comfort_level: 'budget', 'moderate', or 'luxury'
    
    Returns:
        Dictionary with estimated daily expenses
    """
    # Base daily costs by comfort level
    daily_rates = {
        "budget": {"meals": 30, "transport": 15, "activities": 20, "misc": 10},
        "moderate": {"meals": 60, "transport": 30, "activities": 50, "misc": 25},
        "luxury": {"meals": 120, "transport": 60, "activities": 100, "misc": 50}
    }
    
    rates = daily_rates.get(comfort_level, daily_rates["moderate"])
    
    daily_total = sum(rates.values())
    total_estimate = daily_total * num_days
    
    result = {
        "destination": destination,
        "num_days": num_days,
        "comfort_level": comfort_level,
        "daily_breakdown": rates,
        "daily_total": daily_total,
        "total_estimate": total_estimate,
        "currency": "USD"
    }
    
    print(f"[FINANCE] Estimated daily expenses for {destination}: ${daily_total:.2f}/day x {num_days} days = ${total_estimate:.2f}")
    return result


def calculate_price_per_person(total_cost: float, num_people: int) -> Dict[str, Any]:
    """
    Calculate cost per person for group travel.
    
    Args:
        total_cost: Total trip cost
        num_people: Number of travelers
    
    Returns:
        Dictionary with per-person cost
    """
    cost_per_person = total_cost / num_people if num_people > 0 else total_cost
    
    result = {
        "total_cost": total_cost,
        "num_people": num_people,
        "cost_per_person": round(cost_per_person, 2),
        "currency": "USD"
    }
    
    print(f"[FINANCE] Cost per person: ${cost_per_person:.2f} ({num_people} people)")
    return result
