
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
- **Suppliers & Stock:** Manage supplier offers and inventory snapshots using Supabase.
- **Historical Records:** Browse and export historical demand records.

## Technology Stack

- **Language:** Python
- **Application:** Streamlit
- **Data processing:** Pandas, NumPy
- **Visualization:** Matplotlib
- **Machine learning:** Scikit-learn, XGBoost
- **File support:** OpenPyXL
- **Database:** Supabase
- **Database client:** Supabase Python SDK

## Project Structure

```text
supply-chain-inventory-optimization/
├── app.py
├── requirements.txt
├── migrate_json_to_supabase.py
├── README.md
├── data/
│   └── Historical Product Demand.csv
└── src/
    ├── data_processing.py
    ├── demand_analysis.py
    ├── forecast_robustness.py
    ├── forecasting.py
    ├── inventory.py
    └── supply_chain_integrations.py
```

## Requirements

- Python 3.11 or another compatible Python version
- Git
- The project source code and required dataset files
- A Supabase project for supplier and inventory integrations

## Run Locally

1. Clone the repository or open the existing project folder.
2. Create and activate a virtual environment if needed.
3. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

4. Configure your local Supabase credentials as described below.
5. Start the application:

   ```bash
   streamlit run app.py
   ```

6. Open the local URL displayed in the terminal.

## Supabase Configuration

The application uses Supabase for supplier offers and inventory snapshots. Demand datasets and analysis outputs remain managed through the existing application workflow.

For local development, create `.streamlit/secrets.toml` with the following structure:

```toml
[supabase]
url = "YOUR_SUPABASE_PROJECT_URL"
key = "YOUR_SUPABASE_SERVER_SIDE_SECRET_KEY"
```

Replace the placeholders with your own Supabase project values.

**Security:** Never commit `.streamlit/secrets.toml` or publish database credentials. The file is excluded through `.gitignore`.

For deployment, configure the same secrets in your hosting provider's secure secrets settings rather than uploading the local secrets file.

## Dataset Format

The standard demand dataset uses these fields:

- `Product_Code`
- `Warehouse`
- `Product_Category`
- `Date`
- `Order_Demand`

Uploaded files must contain equivalent information mapped to the application's expected fields. Forecast evaluation requires sufficient historical observations for the selected product–warehouse pairs.

## Important Notes

- Forecast accuracy depends on data quality and historical coverage.
- Inventory recommendations are planning estimates, not guarantees of actual stock availability.
- Supplier offers are user-managed records, not verified live supplier quotations.
- Inventory snapshots are application records and are not automatically synchronized with external inventory systems.
- Keep backups of important datasets and project files.

## Deployment

This application can be deployed using Streamlit Community Cloud.

1. Push the project to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Create an app and select this GitHub repository.
4. Choose the `main` branch and `app.py` as the entrypoint.
5. Open the advanced settings and configure the required Supabase secrets securely.
6. Deploy the application and inspect its logs for errors.
7. Test the deployed app's pages and database operations before sharing its URL.

See the [official Streamlit deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) for details.

## Project Status

The application has been run locally, and the Supabase supplier and inventory integrations have been tested. A successful cloud deployment and complete end-to-end verification of the deployed application should be confirmed separately.
