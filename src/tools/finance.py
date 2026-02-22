from typing import List, Dict
from langchain_core.tools import tool


@tool
def calculate_total_cost(items: List[Dict]) -> Dict:
    """
    Calculate total cost from a list of expense items.
    
    Args:
        items: List of dictionaries with 'name' and 'price' keys
    
    Returns:
        Dictionary with total cost and itemized breakdown
    """
    try:
        total = 0.0
        breakdown = []
        
        for item in items:
            name = item.get('name', 'Unknown')
            price = float(item.get('price', 0))
            total += price
            breakdown.append({
                "name": name,
                "price": price
            })
        
        return {
            "total_cost": round(total, 2),
            "item_count": len(items),
            "breakdown": breakdown
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def check_budget_status(current_cost: float, budget: float) -> Dict:
    """
    Check if current spending is within budget.
    
    Args:
        current_cost: Current total expenses
        budget: Available budget
    
    Returns:
        Dictionary with budget status and remaining amount
    """
    try:
        remaining = budget - current_cost
        percentage_used = (current_cost / budget * 100) if budget > 0 else 0
        
        return {
            "budget": budget,
            "current_cost": current_cost,
            "remaining": round(remaining, 2),
            "percentage_used": round(percentage_used, 2),
            "within_budget": remaining >= 0,
            "status": "Within budget" if remaining >= 0 else "Over budget"
        }
    except Exception as e:
        return {"error": str(e)}


@tool
def estimate_daily_expenses(destination: str, days: int, category: str = "moderate") -> Dict:
    """
    Estimate daily expenses for a destination.
    
    Args:
        destination: Travel destination
        days: Number of days
        category: Budget category - "budget", "moderate", or "luxury"
    
    Returns:
        Dictionary with estimated costs per day and total
    """
    # Base estimates per day (in USD)
    estimates = {
        "budget": {
            "accommodation": 30,
            "food": 15,
            "activities": 10,
            "transport": 10
        },
        "moderate": {
            "accommodation": 80,
            "food": 40,
            "activities": 30,
            "transport": 20
        },
        "luxury": {
            "accommodation": 200,
            "food": 100,
            "activities": 80,
            "transport": 50
        }
    }
    
    try:
        category_estimates = estimates.get(category, estimates["moderate"])
        daily_total = sum(category_estimates.values())
        total_cost = daily_total * days
        
        return {
            "destination": destination,
            "days": days,
            "category": category,
            "daily_breakdown": category_estimates,
            "daily_total": daily_total,
            "total_estimated_cost": total_cost
        }
    except Exception as e:
        return {"error": str(e)}
