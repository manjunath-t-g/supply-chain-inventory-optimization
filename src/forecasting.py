
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error
from xgboost import XGBRegressor


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLEANED_FILE = PROJECT_ROOT / "data" / "processed" / "cleaned_demand.csv"


def load_weekly_demand():
    """Aggregate individual orders into weekly product demand."""

    if not CLEANED_FILE.exists():
        raise FileNotFoundError(
            f"Cleaned data not found: {CLEANED_FILE}. "
            "Run python src\\data_processing.py first."
        )

    df = pd.read_csv(CLEANED_FILE, parse_dates=["Date"])

    weekly = (
        df.groupby(
            [
                "Product_Code",
                "Warehouse",
                "Product_Category",
                pd.Grouper(key="Date", freq="W"),
            ],
            as_index=False,
        )["Order_Demand"]
        .sum()
        .rename(columns={"Order_Demand": "Demand"})
        .sort_values(["Product_Code", "Warehouse", "Date"])
        .reset_index(drop=True)
    )

    return weekly


def add_features(group):
    """Create lag and calendar features using past demand only."""

    group = group.sort_values("Date").copy()

    # Past demand values; shift prevents the current target leaking in.
    group["lag_1"] = group["Demand"].shift(1)
    group["lag_2"] = group["Demand"].shift(2)
    group["lag_4"] = group["Demand"].shift(4)
    group["rolling_mean_4"] = group["Demand"].shift(1).rolling(4).mean()

    group["month"] = group["Date"].dt.month
    group["week_of_year"] = group["Date"].dt.isocalendar().week.astype(int)

    return group



def evaluate_product(product_code, warehouse, weekly_data=None):
    """Evaluate baseline and XGBoost for one product-warehouse pair."""

    weekly = (
        weekly_data
        if weekly_data is not None
        else load_weekly_demand()
    )


    group = weekly[
        (weekly["Product_Code"] == product_code)
        & (weekly["Warehouse"] == warehouse)
    ].copy()

    if group.empty:
        raise ValueError(
            f"No records found for {product_code} at {warehouse}."
        )

    # Include zero-demand weeks between the first and last observed weeks.
    # These are weeks with no recorded orders, not confirmed inventory sales.
    group = (
        group.set_index("Date")
        .resample("W")["Demand"]
        .sum()
        .to_frame()
        .reset_index()
    )

    group["Product_Code"] = product_code
    group["Warehouse"] = warehouse
    group = add_features(group).dropna().reset_index(drop=True)

    if len(group) < 20:
        raise ValueError(
            f"Only {len(group)} usable weekly observations are available. "
            "Choose a product with more history."
        )

    feature_columns = [
        "lag_1",
        "lag_2",
        "lag_4",
        "rolling_mean_4",
        "month",
        "week_of_year",
    ]

    # Keep the last 20% for testing, in chronological order.
    split_index = int(len(group) * 0.8)
    train = group.iloc[:split_index].copy()
    test = group.iloc[split_index:].copy()

    if train.empty or test.empty:
        raise ValueError("Not enough data for a train/test split.")

    X_train = train[feature_columns]
    y_train = train["Demand"]
    X_test = test[feature_columns]
    y_test = test["Demand"]

    
    # Method 1: historical-average baseline
    baseline_predictions = np.full(
        len(test), y_train.mean(), dtype=float
    )

    # Method 2: last week's observed demand
    last_week_predictions = test["lag_1"].to_numpy()

    # Method 3: average of the previous four observed weeks
    moving_average_predictions = test["rolling_mean_4"].to_numpy()

    # Method 4: XGBoost machine-learning model
    model = XGBRegressor(
        n_estimators=250,
        max_depth=4,
        learning_rate=0.05,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=4,
    )

    model.fit(X_train, y_train)
    predictions = np.maximum(model.predict(X_test), 0)

    def calculate_metrics(actual, predicted):
        mae = mean_absolute_error(actual, predicted)
        total_actual = np.abs(actual).sum()

        wape = (
            np.abs(actual - predicted).sum() / total_actual * 100
            if total_actual > 0
            else np.nan
        )

        return {
            "MAE": float(mae),
            "WAPE_percent": float(wape),
        }
    actual = y_test.to_numpy()

    results = pd.DataFrame({
        "Date": test["Date"].to_numpy(),
        "Actual_Demand": actual,
        "Historical_Mean_Forecast": baseline_predictions,
        "Last_Week_Forecast": last_week_predictions,
        "Moving_Average_4_Weeks": moving_average_predictions,
        "XGBoost_Forecast": predictions,
    })

    metrics = {
        "product": product_code,
        "warehouse": warehouse,
        "training_weeks": len(train),
        "testing_weeks": len(test),
        "historical_mean": calculate_metrics(
            actual, baseline_predictions
        ),
        "last_week": calculate_metrics(
            actual, last_week_predictions
        ),
        "moving_average_4_weeks": calculate_metrics(
            actual, moving_average_predictions
        ),
        "xgboost": calculate_metrics(actual, predictions),
    }

    return results, metrics




if __name__ == "__main__":
    weekly = load_weekly_demand()

    print("=== MULTI-PRODUCT FORECAST EVALUATION ===")
    print(f"Weekly records: {len(weekly):,}")
    print(f"Unique products: {weekly['Product_Code'].nunique():,}")
    print(f"Warehouses: {weekly['Warehouse'].nunique():,}")

    # Find product-warehouse pairs with sufficient history.
    pair_counts = (
        weekly.groupby(["Product_Code", "Warehouse"])
        .size()
    )

    eligible_pairs = (
        pair_counts[pair_counts >= 52]
        .reset_index()[["Product_Code", "Warehouse"]]
        .sort_values(["Product_Code", "Warehouse"])
    )

    # Use a reproducible sample for the first experiment.
    sample_size = min(100, len(eligible_pairs))

    sampled_pairs = eligible_pairs.sample(
        n=sample_size,
        random_state=42,
    )

    print(f"\nEligible pairs: {len(eligible_pairs):,}")
    print(f"Pairs selected for evaluation: {sample_size}")

    detailed_results = []
    pair_metrics = []
    failed_pairs = []

    methods = {
        "Historical_Mean": "historical_mean",
        "Last_Week": "last_week",
        "Moving_Average_4_Weeks": "moving_average_4_weeks",
        "XGBoost": "xgboost",
    }

    for index, pair in enumerate(
        sampled_pairs.itertuples(index=False, name=None),
        start=1,
    ):
        product_code, warehouse = pair

        try:
            predictions, metrics = evaluate_product(
                product_code,
                warehouse,
                weekly_data=weekly,
            )

            predictions.insert(0, "Warehouse", warehouse)
            predictions.insert(0, "Product_Code", product_code)
            detailed_results.append(predictions)

            for method_name, metric_key in methods.items():
                method_metrics = metrics[metric_key]

                pair_metrics.append({
                    "Product_Code": product_code,
                    "Warehouse": warehouse,
                    "Method": method_name,
                    "Training_Weeks": metrics["training_weeks"],
                    "Testing_Weeks": metrics["testing_weeks"],
                    "MAE": method_metrics["MAE"],
                    "WAPE_percent": method_metrics["WAPE_percent"],
                })

            if index % 10 == 0 or index == sample_size:
                print(
                    f"Evaluated {index}/{sample_size} "
                    "product-warehouse pairs"
                )

        except (ValueError, KeyError) as error:
            failed_pairs.append({
                "Product_Code": product_code,
                "Warehouse": warehouse,
                "Error": str(error),
            })

    if not pair_metrics:
        raise RuntimeError(
            "No pairs were evaluated successfully. "
            "Check the dataset and error messages."
        )

    output_dir = PROJECT_ROOT / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save individual forecasts and actual values.
    detailed_file = output_dir / "forecast_evaluation.csv"
    pd.concat(detailed_results, ignore_index=True).to_csv(
        detailed_file,
        index=False,
    )

    # Save metrics for every method and evaluated pair.
    metrics_df = pd.DataFrame(pair_metrics)

    # Count how often each method achieves the lowest MAE
    # for an individual product-warehouse pair.
    best_indices = metrics_df.groupby(
        ["Product_Code", "Warehouse"]
    )["MAE"].idxmin()

    winner_counts = (
        metrics_df.loc[best_indices, "Method"]
        .value_counts()
        .to_dict()
    )

    comparison = (
        metrics_df.groupby("Method")
        .agg(
            Pairs_Evaluated=("MAE", "count"),
            Mean_MAE=("MAE", "mean"),
            Median_MAE=("MAE", "median"),
            Mean_WAPE_percent=("WAPE_percent", "mean"),
            Median_WAPE_percent=("WAPE_percent", "median"),
        )
        .reset_index()
    )

    comparison["Lowest_MAE_Wins"] = (
        comparison["Method"]
        .map(winner_counts)
        .fillna(0)
        .astype(int)
    )

    comparison = comparison.sort_values(
        "Mean_MAE"
    ).reset_index(drop=True)

    comparison_file = (
        output_dir / "forecast_model_comparison.csv"
    )
    comparison.to_csv(comparison_file, index=False)

    # Save detailed per-pair metrics as a separate file.
    pair_metrics_file = (
        output_dir / "forecast_pair_metrics.csv"
    )
    metrics_df.to_csv(pair_metrics_file, index=False)

    print("\n=== MODEL COMPARISON ===")
    print(comparison.round(2).to_string(index=False))

    print("\n=== EVALUATION SUMMARY ===")
    print(f"Successful pairs: {metrics_df['Product_Code'].nunique()}")
    print(f"Failed pairs: {len(failed_pairs)}")

    print(f"\nDetailed forecasts saved to: {detailed_file}")
    print(f"Model comparison saved to: {comparison_file}")
    print(f"Per-pair metrics saved to: {pair_metrics_file}")

    if failed_pairs:
        failed_file = output_dir / "forecast_failed_pairs.csv"
        pd.DataFrame(failed_pairs).to_csv(
            failed_file,
            index=False,
        )
        print(f"Failed-pair details saved to: {failed_file}")

