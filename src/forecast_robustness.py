
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor

from forecasting import load_weekly_demand

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "forecast_robustness_comparison.csv"
)


def evaluate_pair(product_code, warehouse, weekly_data):
    group = weekly_data[
        (weekly_data["Product_Code"] == product_code)
        & (weekly_data["Warehouse"] == warehouse)
    ].copy()

    if group.empty:
        return None

    group = (
        group.set_index("Date")["Demand"]
        .resample("W")
        .sum()
        .to_frame()
        .reset_index()
    )

    if len(group) < 52:
        return None

    split = int(len(group) * 0.8)
    train = group.iloc[:split].copy()
    test = group.iloc[split:].copy()

    if train.empty or test.empty:
        return None

    features = pd.DataFrame(index=group.index)
    features["lag_1"] = group["Demand"].shift(1)
    features["lag_2"] = group["Demand"].shift(2)
    features["lag_4"] = group["Demand"].shift(4)
    features["rolling_mean_4"] = (
        group["Demand"].shift(1).rolling(4).mean()
    )
    features["month"] = group["Date"].dt.month
    features["week_of_year"] = (
        group["Date"].dt.isocalendar().week.astype(int)
    )

    usable = group.join(features).dropna().reset_index(drop=True)
    split_usable = int(len(usable) * 0.8)
    train = usable.iloc[:split_usable].copy()
    test = usable.iloc[split_usable:].copy()

    if len(train) < 20 or test.empty:
        return None

    columns = [
        "lag_1",
        "lag_2",
        "lag_4",
        "rolling_mean_4",
        "month",
        "week_of_year",
    ]

    # Calculate the cap from training targets only.
    cap = train["Demand"].quantile(0.95)

    actual = test["Demand"].to_numpy()
    predictions_by_method = {}

    # Historical mean trained on original demand.
    predictions_by_method["XGBoost_Original"] = None

    original_model = XGBRegressor(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=4,
    )
    original_model.fit(train[columns], train["Demand"])
    predictions_by_method["XGBoost_Original"] = np.maximum(
        original_model.predict(test[columns]), 0
    )

    # Train a separate model with capped training targets.
    capped_model = XGBRegressor(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=4,
    )
    capped_targets = train["Demand"].clip(upper=cap)
    capped_model.fit(train[columns], capped_targets)
    predictions_by_method["XGBoost_Capped_Training"] = np.maximum(
        capped_model.predict(test[columns]), 0
    )

    rows = []

    for method, predicted in predictions_by_method.items():
        mae = mean_absolute_error(actual, predicted)
        total_actual = np.abs(actual).sum()
        wape = (
            np.abs(actual - predicted).sum() / total_actual * 100
            if total_actual > 0
            else np.nan
        )

        rows.append({
            "Product_Code": product_code,
            "Warehouse": warehouse,
            "Method": method,
            "Training_Weeks": len(train),
            "Testing_Weeks": len(test),
            "Training_95th_Percentile_Cap": cap,
            "MAE": mae,
            "WAPE_percent": wape,
        })

    return rows


def main():
    weekly = load_weekly_demand()

    pair_counts = weekly.groupby(
        ["Product_Code", "Warehouse"]
    ).size()

    eligible = (
        pair_counts[pair_counts >= 52]
        .reset_index()[["Product_Code", "Warehouse"]]
    )

    selected = eligible.sample(
        n=min(100, len(eligible)),
        random_state=42,
    )

    all_results = []

    for number, pair in enumerate(
        selected.itertuples(index=False, name=None),
        start=1,
    ):
        product, warehouse = pair

        try:
            result = evaluate_pair(product, warehouse, weekly)
            if result:
                all_results.extend(result)
        except (ValueError, KeyError) as error:
            print(f"Skipped {product} / {warehouse}: {error}")

        if number % 10 == 0 or number == len(selected):
            print(f"Processed {number}/{len(selected)} pairs")

    if not all_results:
        raise RuntimeError("No robustness results were generated.")

    results = pd.DataFrame(all_results)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(OUTPUT_FILE, index=False)

    summary = (
        results.groupby("Method")
        .agg(
            Pairs_Evaluated=("MAE", "count"),
            Mean_MAE=("MAE", "mean"),
            Median_MAE=("MAE", "median"),
            Mean_WAPE_percent=("WAPE_percent", "mean"),
            Median_WAPE_percent=("WAPE_percent", "median"),
        )
        .reset_index()
    )


    print("\n=== ROBUSTNESS EXPERIMENT ===")
    print(summary.round(2).to_string(index=False))

    pivot = results.pivot(
        index=["Product_Code", "Warehouse"],
        columns="Method",
        values="MAE",
    ).dropna()

    pivot["Capped_MAE_Change"] = (
        pivot["XGBoost_Capped_Training"]
        - pivot["XGBoost_Original"]
    )

    improved = (pivot["Capped_MAE_Change"] < 0).sum()
    worsened = (pivot["Capped_MAE_Change"] > 0).sum()
    unchanged = (pivot["Capped_MAE_Change"] == 0).sum()

    print("\n=== PAIR-LEVEL MAE RESULTS ===")
    print(f"Pairs improved: {improved}")
    print(f"Pairs worsened: {worsened}")
    print(f"Pairs unchanged: {unchanged}")

    print("\nLargest MAE improvements:")
    print(
        pivot.sort_values("Capped_MAE_Change")
        .head(10)
        .round(2)
        .to_string()
    )

    print("\nLargest MAE regressions:")
    print(
        pivot.sort_values("Capped_MAE_Change", ascending=False)
        .head(10)
        .round(2)
        .to_string()
    )

    print(f"\nDetailed results saved to: {OUTPUT_FILE}")



if __name__ == "__main__":
    main()
