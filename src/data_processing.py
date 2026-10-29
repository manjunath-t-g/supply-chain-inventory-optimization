from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = PROJECT_ROOT / "data" / "Historical Product Demand.csv"


def load_and_clean_data(file_path=DATA_FILE):
    """Load and clean historical product-demand data."""

    if not Path(file_path).exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}\n"
            "Place Historical Product Demand.csv inside the data folder."
        )

    df = pd.read_csv(file_path)

    # Normalize column names
    df.columns = df.columns.str.strip()

    required_columns = [
        "Product_Code",
        "Warehouse",
        "Product_Category",
        "Date",
        "Order_Demand",
    ]

    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}\n"
            f"Columns found: {df.columns.tolist()}"
        )

    original_rows = len(df)

    # Clean text fields
    for column in ["Product_Code", "Warehouse", "Product_Category"]:
        df[column] = df[column].astype("string").str.strip()

    # Convert dates; invalid or missing dates become NaT
    df["Date"] = pd.to_datetime(
        df["Date"], errors="coerce"
    )

    # Handle demand values stored as text, including parentheses
    demand = df["Order_Demand"].astype("string").str.strip()
    demand = demand.str.replace(",", "", regex=False)

    negative_parentheses = demand.str.match(
        r"^\(.*\)$", na=False
    )
    demand = demand.str.replace(
        r"^\((.*)\)$", r"\1", regex=True
    )

    df["Order_Demand"] = pd.to_numeric(
        demand, errors="coerce"
    )

    df.loc[negative_parentheses, "Order_Demand"] *= -1

    # Remove rows without usable product, warehouse, date, or demand
    df = df.dropna(
        subset=[
            "Product_Code",
            "Warehouse",
            "Date",
            "Order_Demand",
        ]
    )

    df = df[
        (df["Product_Code"] != "")
        & (df["Warehouse"] != "")
    ].copy()

    # Add useful calendar features
    df["Year"] = df["Date"].dt.year
    df["Month"] = df["Date"].dt.month
    df["Day"] = df["Date"].dt.day
    df["YearMonth"] = df["Date"].dt.to_period("M").astype(str)

    # Sort records chronologically
    df = df.sort_values(
        ["Product_Code", "Warehouse", "Date"]
    ).reset_index(drop=True)

    report = {
        "original_rows": original_rows,
        "cleaned_rows": len(df),
        "removed_rows": original_rows - len(df),
        "missing_dates_before_cleaning": int(
            pd.isna(pd.to_datetime(
                pd.read_csv(file_path, usecols=["Date"])["Date"],
                errors="coerce",
            )).sum()
        ),
        "unique_products": int(df["Product_Code"].nunique()),
        "unique_warehouses": int(df["Warehouse"].nunique()),
        "unique_product_warehouse_pairs": int(
            df[["Product_Code", "Warehouse"]]
            .drop_duplicates()
            .shape[0]
        ),
        "date_from": df["Date"].min(),
        "date_to": df["Date"].max(),
        "total_demand": float(df["Order_Demand"].sum()),
    }

    return df, report


if __name__ == "__main__":
    cleaned_data, quality_report = load_and_clean_data()

    # Create the processed-data directory if it doesn't exist
    processed_dir = PROJECT_ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Save cleaned historical demand
    output_file = processed_dir / "cleaned_demand.csv"
    cleaned_data.to_csv(output_file, index=False)

    print("\n=== DATA QUALITY REPORT ===")
    for key, value in quality_report.items():
        print(f"{key}: {value}")

    print(f"\nCleaned dataset saved to: {output_file}")
    print("\n=== CLEANED DATA PREVIEW ===")
    print(cleaned_data.head(10).to_string(index=False))
