# 📦 Supply Chain & Inventory Optimization

A data-driven Streamlit application for demand analytics, forecasting evaluation, inventory planning, and supplier management.

## Features

- **Project Overview:** View demand summaries, trends, warehouse demand, and top products.
- **Upload & Map Data:** Upload CSV or Excel files, preview records, map columns, and validate data.
- **Demand Analytics:** Explore historical demand and weekly trends.
- **Inventory Optimization:** Estimate safety stock, reorder points, target stock, and suggested order quantities.
- **Forecast Model Comparison:** Evaluate forecasting methods using historical demand.
- **Demand Pattern Analysis:** Classify demand based on frequency and variability.
- **Forecast Robustness:** Compare forecasting performance under demand-capping scenarios.
- **Suppliers & Stock:** Record local inventory snapshots and compare manually entered supplier offers.
- **Historical Records:** Browse and export historical demand records.

## Technology Stack

- Python
- Streamlit
- Pandas
- NumPy
- Matplotlib
- Scikit-learn
- XGBoost
- OpenPyXL

## Requirements

- Python installed on your computer
- The project source code and required dataset files
- Dependencies listed in `requirements.txt`

## Run Locally

1. Open the project folder in VS Code.
2. Activate your virtual environment.
3. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Start the application:

   ```bash
   streamlit run app.py
   ```

5. Open the local URL displayed in the terminal.

## Dataset Format

The standard demand dataset uses these fields:

- `Product_Code`
- `Warehouse`
- `Product_Category`
- `Date`
- `Order_Demand`

Uploaded files must contain equivalent information mapped to the application's expected fields. Forecast evaluation requires sufficient historical observations for the selected product–warehouse pairs.

## Important Notes

- Forecast accuracy depends on the quality and history of the supplied data.
- Inventory recommendations are planning estimates, not guarantees of actual stock availability.
- Supplier offers and stock snapshots are stored locally in the demonstration application; they are not verified live supplier quotations or external inventory API data.
- Keep original datasets and project backups safe.

## Project Status

The application has been tested locally. Complete a fresh-environment installation and final end-to-end checks before publishing the repository.
