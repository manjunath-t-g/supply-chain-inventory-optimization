
from math import ceil, sqrt


def calculate_inventory_policy(
    weekly_demand,
    current_stock,
    lead_time_days,
    review_period_days=7,
    service_level_z=1.65,
):
    """
    Calculate a basic inventory policy.

    weekly_demand:
        Historical weekly demand observations (units per week).

    current_stock:
        Current available stock in units.

    lead_time_days:
        Supplier lead time in days.

    review_period_days:
        How often inventory is reviewed.

    service_level_z:
        1.65 is approximately a 95% one-sided service factor
        under a normal-demand approximation.
    """

    if not weekly_demand:
        raise ValueError("Provide at least one weekly demand value.")

    if any(value < 0 for value in weekly_demand):
        raise ValueError("Weekly demand cannot be negative.")

    if current_stock < 0:
        raise ValueError("Current stock cannot be negative.")

    if lead_time_days < 0:
        raise ValueError("Lead time cannot be negative.")

    if review_period_days <= 0:
        raise ValueError("Review period must be greater than zero.")

    if service_level_z < 0:
        raise ValueError("Service-level factor cannot be negative.")

    average_weekly_demand = sum(weekly_demand) / len(weekly_demand)

    if len(weekly_demand) > 1:
        mean = average_weekly_demand
        variance = sum(
            (value - mean) ** 2 for value in weekly_demand
        ) / (len(weekly_demand) - 1)
        weekly_demand_std = sqrt(variance)
    else:
        weekly_demand_std = 0.0

    average_daily_demand = average_weekly_demand / 7
    lead_time_weeks = lead_time_days / 7
    review_period_weeks = review_period_days / 7

    # Approximate demand variability during lead time plus review period.
    protection_period_weeks = lead_time_weeks + review_period_weeks

    safety_stock = (
        service_level_z
        * weekly_demand_std
        * sqrt(protection_period_weeks)
    )

    reorder_point = (
        average_weekly_demand * lead_time_weeks
        + safety_stock
    )

    target_stock = (
        average_weekly_demand * protection_period_weeks
        + safety_stock
    )

    reorder_point = ceil(reorder_point)
    safety_stock = ceil(safety_stock)
    target_stock = ceil(target_stock)

    reorder_needed = current_stock <= reorder_point

    suggested_order_quantity = (
        max(0, target_stock - current_stock)
        if reorder_needed
        else 0
    )

    return {
        "average_weekly_demand": round(average_weekly_demand, 2),
        "average_daily_demand": round(average_daily_demand, 2),
        "weekly_demand_std": round(weekly_demand_std, 2),
        "lead_time_days": lead_time_days,
        "safety_stock_units": safety_stock,
        "reorder_point_units": reorder_point,
        "target_stock_units": target_stock,
        "current_stock_units": current_stock,
        "reorder_needed": reorder_needed,
        "suggested_order_quantity_units": suggested_order_quantity,
    }


if __name__ == "__main__":
    # DEMO ONLY — replace these example values with real inventory data.
    demo_weekly_demand = [
        100, 120, 90, 140, 110, 130, 95, 125
    ]

    result = calculate_inventory_policy(
        weekly_demand=demo_weekly_demand,
        current_stock=200,
        lead_time_days=14,
    )

    print("=== INVENTORY POLICY DEMO ===")
    print("WARNING: Example values only; not real inventory data.")

    for key, value in result.items():
        print(f"{key}: {value}")
