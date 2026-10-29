
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_FILE = (
    PROJECT_ROOT / "data" / "processed" / "cleaned_demand.csv"
)
OUTPUT_FILE = (
    PROJECT_ROOT / "data" / "processed" / "demand_pattern_analysis.csv"
)


def analyze_demand_patterns():
    if not CLEANED_FILE.exists():
        raise FileNotFoundError(
            "Cleaned dataset not found. Run "
            "python src\\data_processing.py first."
        )

    df = pd.read_csv(CLEANED_FILE, parse_dates=["Date"])

    weekly = (
        df.groupby(
            [
                "Product_Code",
                "Warehouse",
                pd.Grouper(key="Date", freq="W"),
            ]
        )["Order_Demand"]
        .sum()
        .reset_index()
        .sort_values(["Product_Code", "Warehouse", "Date"])
    )

    results = []

    for (product, warehouse), group in weekly.groupby(
        ["Product_Code", "Warehouse"]
    ):
        # Add missing weeks as zero recorded demand.
        demand = (
            group.set_index("Date")["Order_Demand"]
            .resample("W")
            .sum()
        )

        if len(demand) < 20:
            continue

        positive = demand[demand > 0]

        if positive.empty:
            continue

        average_demand = demand.mean()
        demand_std = demand.std(ddof=1)
        nonzero_fraction = (demand > 0).mean()

        # Demand variability relative to its mean.
        cv_squared = (
            (demand_std / average_demand) ** 2
            if average_demand > 0
            else float("nan")
        )

        # Average interval between weeks with positive demand.
        positive_positions = [
            i for i, value in enumerate(demand.to_numpy())
            if value > 0
        ]

        intervals = [
            positive_positions[i] - positive_positions[i - 1]
            for i in range(1, len(positive_positions))
        ]

        average_interval = (
            sum(intervals) / len(intervals)
            if intervals
            else float("nan")
        )
        
        # Classify demand using the observed frequency and variability.
        if nonzero_fraction >= 0.8:
            demand_pattern = "Frequent"
        elif nonzero_fraction < 0.2:
            if cv_squared >= 0.5:
                demand_pattern = "Lumpy / Highly Intermittent"
            else:
                demand_pattern = "Highly Intermittent"
        elif nonzero_fraction < 0.5:
            if cv_squared >= 0.5:
                demand_pattern = "Lumpy / Intermittent"
            else:
                demand_pattern = "Intermittent"
        else:
            if cv_squared >= 0.5:
                demand_pattern = "Variable Frequent"
            else:
                demand_pattern = "Frequent"



        results.append({
            "Product_Code": product,
            "Warehouse": warehouse,
            "Demand_Pattern": demand_pattern,
            "Weekly_Observations": len(demand),
            "Weeks_With_Demand": int((demand > 0).sum()),
            "Nonzero_Week_Fraction": round(nonzero_fraction, 4),
            "Average_Weekly_Demand": round(average_demand, 2),
            "Demand_Std": round(demand_std, 2),
            "CV_Squared": round(cv_squared, 4),
            "Average_Interval_Between_Demand_Weeks": round(
                average_interval, 2
            ),
            "Maximum_Weekly_Demand": round(demand.max(), 2),
        })


    output = pd.DataFrame(results)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    output.to_csv(OUTPUT_FILE, index=False)


    print("=== DEMAND PATTERN ANALYSIS ===")
    print(f"Product-warehouse pairs analyzed: {len(output):,}")

    if not output.empty:
        print("\n=== DEMAND PATTERN COUNTS ===")
        print(output["Demand_Pattern"].value_counts().to_string())

        print(
            "\nLowest nonzero-demand fractions:\n",
            output.sort_values("Nonzero_Week_Fraction")
            .head(10)
            .to_string(index=False),
        )


        print(
            "\nHighest demand variability:\n",
            output.sort_values("CV_Squared", ascending=False)
            .head(10)
            .to_string(index=False),
        )

    print(f"\nResults saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    analyze_demand_patterns()
