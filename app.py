from pathlib import Path

import pandas as pd
import streamlit as st

from src.inventory import calculate_inventory_policy
from src.supply_chain_integrations import (
    compare_suppliers,
    get_inventory_snapshot,
    get_stock,
    get_suppliers,
    save_suppliers,
    update_inventory,
)

PROJECT_ROOT = Path(__file__).resolve().parent
CLEANED_FILE = PROJECT_ROOT / "data" / "processed" / "cleaned_demand.csv"
COMPARISON_FILE = PROJECT_ROOT / "data" / "processed" / "forecast_model_comparison.csv"
PATTERN_FILE = PROJECT_ROOT / "data" / "processed" / "demand_pattern_analysis.csv"
ROBUSTNESS_FILE = PROJECT_ROOT / "data" / "processed" / "forecast_robustness_comparison.csv"

st.set_page_config(
    page_title="AI Supply Chain & Inventory Optimization",
    page_icon="📦",
    layout="wide",
)


# --------------------------------------------------
# GLOBAL STYLE — THEME AWARE
# --------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        /* Follow Streamlit's selected theme */
        --sc-bg: var(--background-color);
        --sc-surface: var(--secondary-background-color);
        --sc-ink: var(--text-color);
        --sc-muted: color-mix(in srgb, var(--text-color) 65%, transparent);

        /* Permanent brand identity */
        --sc-navy: #0B1424;
        --sc-blue: #2563EB;
        --sc-cyan: #39D9D0;
        --sc-border: color-mix(in srgb, var(--text-color) 16%, transparent);
    }

    @keyframes sc-fade-up {
        from { opacity: 0; transform: translateY(12px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes sc-soft-glow {
        0%, 100% { box-shadow: 0 0 0 rgba(57, 217, 208, 0); }
        50% { box-shadow: 0 0 18px rgba(57, 217, 208, 0.12); }
    }

    @keyframes sc-pulse-dot {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: .55; transform: scale(.82); }
    }

    @media (prefers-reduced-motion: reduce) {
        *, *::before, *::after {
            animation-duration: 0.01ms !important;
            animation-iteration-count: 1 !important;
            scroll-behavior: auto !important;
            transition-duration: 0.01ms !important;
        }
    }

    html { scroll-behavior: smooth; }

    /* Main application background */
    [data-testid="stAppViewContainer"] {
    background: var(--sc-bg);
    color: var(--sc-ink);
}

    [data-testid="stMainBlockContainer"] {
        animation: sc-fade-up .48s ease-out both;
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        color: var(--sc-ink);
    }

    /* Keep branded navy sidebar in both themes */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1424 0%, #101D31 58%, #0D1728 100%);
        border-right: 1px solid rgba(148, 163, 184, 0.14);
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.4rem;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown {
        color: #D7E3F2;
    }

    [data-testid="stSidebar"] hr {
        border-color: #334155;
    }

    .sidebar-brand {
        font-size: 20px;
        font-weight: 800;
        color: #F8FAFC;
        line-height: 1.4;
        letter-spacing: -.35px;
        text-shadow: 0 0 22px rgba(57, 217, 208, .12);
    }

    .sidebar-subtitle {
        font-size: 10px;
        letter-spacing: 1.5px;
        color: #48D9D0;
        margin-top: 5px;
        margin-bottom: 20px;
    }

    .sidebar-footer {
        border-top: 1px solid #334155;
        padding-top: 14px;
        margin-top: 24px;
        color: #94A3B8;
        font-size: 11px;
    }

    .sidebar-status {
        color: #48D9D0;
        font-weight: 600;
    }

    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        min-height: 42px;
        text-align: left;
        justify-content: flex-start;
        border: 1px solid transparent;
        border-radius: 10px;
        padding: 8px 12px;
        background-color: transparent;
        color: #D7E3F2;
        font-size: 14px;
        transition: background-color .22s ease, color .22s ease,
                    border-color .22s ease, transform .22s ease,
                    box-shadow .22s ease;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(100deg, rgba(30, 64, 94, .9), rgba(30, 41, 59, .72));
        color: #FFFFFF;
        border-color: rgba(57, 217, 208, .25);
        transform: translateX(3px);
        box-shadow: 0 5px 16px rgba(0, 0, 0, .12);
    }

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: linear-gradient(100deg, #164E63, #155E75);
        color: #FFFFFF;
        border: 1px solid rgba(57, 217, 208, .2);
        border-left: 3px solid #48D9D0;
        font-weight: 650;
        box-shadow: 0 7px 20px rgba(8, 145, 178, .14);
        animation: sc-soft-glow 3.6s ease-in-out infinite;
    }

    /* Metric cards */
    [data-testid="stMetric"] {
        background: var(--sc-surface);
        border: 1px solid var(--sc-border);
        border-radius: 15px;
        padding: 16px 18px;
        box-shadow: 0 5px 18px rgba(15, 23, 42, .035);
        transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
        animation: sc-fade-up .55s ease-out both;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        border-color: rgba(37, 99, 235, .35);
        box-shadow: 0 12px 28px rgba(15, 23, 42, .08);
    }

    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] p {
        color: var(--sc-muted);
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        color: var(--sc-ink);
        font-weight: 750;
        letter-spacing: -.7px;
        font-size: clamp(1.05rem, 1.8vw, 1.65rem);
        line-height: 1.2;
        overflow-wrap: anywhere;
        font-variant-numeric: tabular-nums;
    }

    [data-testid="stMetricLabel"] p {
        font-size: .82rem;
    }

    /* Charts, tables and form surfaces */
    [data-testid="stPlotlyChart"],
    [data-testid="stVegaLiteChart"],
    [data-testid="stArrowVegaLiteChart"],
    [data-testid="stDataFrame"],
    [data-testid="stTable"],
    [data-testid="stForm"],
    [data-testid="stExpander"] {
        border-radius: 14px;
    }

    [data-testid="stPlotlyChart"],
    [data-testid="stVegaLiteChart"],
    [data-testid="stArrowVegaLiteChart"] {
        animation: sc-fade-up .7s ease-out both;
    }

    [data-testid="stDataFrame"] {
        border: 1px solid var(--sc-border);
        overflow: hidden;
    }

    /* Tabs */
    [data-testid="stTabs"] button {
        transition: color .2s ease, background-color .2s ease;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--primary-color);
        font-weight: 700;
    }

    /* Buttons */
    .stButton > button,
    .stDownloadButton > button,
    [data-testid="stFormSubmitButton"] > button {
        border-radius: 10px;
        transition: transform .18s ease, box-shadow .18s ease, filter .18s ease;
        white-space: normal;
        overflow-wrap: anywhere;
    }

    /* Overview feature cards */
    .sc-feature-title {
        color: var(--sc-ink);
        font-size: 1.1rem;
        font-weight: 750;
        line-height: 1.4;
        margin-bottom: 10px;
    }

    .sc-feature-description {
        color: var(--sc-muted);
        font-size: .95rem;
        line-height: 1.65;
    }

    .sc-feature-card,
    .st-key-overview_cards [data-testid="stButton"] > button {
        min-height: 140px;
        height: 100%;
        padding: 20px;
        border: 1px solid var(--sc-border);
        border-radius: 14px;
        background: var(--sc-surface);
        color: var(--sc-ink);
        box-shadow: 0 5px 18px rgba(15, 23, 42, .035);
        transition: transform .22s ease,
                    box-shadow .22s ease,
                    border-color .22s ease;
    }

    .st-key-overview_cards [data-testid="stButton"] > button {
        width: 100%;
        text-align: left;
        justify-content: flex-start;
        align-items: flex-start;
        white-space: normal;
    }

    .st-key-overview_cards [data-testid="stButton"] > button p {
        white-space: pre-wrap;
        overflow-wrap: anywhere;
        text-align: left;
        font-size: .95rem;
        line-height: 1.65;
    }

    .st-key-overview_cards [data-testid="stButton"] > button:hover,
    .sc-feature-card:hover {
        transform: translateY(-4px);
        border-color: rgba(37, 99, 235, .38);
        box-shadow: 0 12px 26px rgba(15, 23, 42, .08);
    }

    .sc-feature-heading {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        color: var(--sc-ink);
        font-size: .94rem;
        font-weight: 750;
        line-height: 1.45;
        margin-bottom: 8px;
    }

    .sc-feature-icon { flex: 0 0 auto; }

    .sc-feature-description {
        color: var(--sc-muted);
        font-size: .8rem;
        line-height: 1.55;
    }

    [data-testid="stStatusWidget"] {
        animation: sc-pulse-dot 2.4s ease-in-out infinite;
    }
    /* Theme-aware sidebar filter selections */
    [data-testid="stSidebar"] [data-baseweb="tag"] {
        background-color: var(--sc-blue) !important;
        color: #FFFFFF !important;
        border: 1px solid var(--sc-cyan);
    }
    
    [data-testid="stSidebar"] [data-baseweb="tag"] span {
        color: #FFFFFF !important;
    }
    
    [data-testid="stSidebar"] [data-baseweb="tag"] svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# SIDEBAR BRAND AND NAVIGATION
# --------------------------------------------------
st.sidebar.markdown(
    """
    <div class="sidebar-brand">📦 SUPPLYCHAIN AI</div>
    <div class="sidebar-subtitle">INTELLIGENCE PLATFORM</div>
    """,
    unsafe_allow_html=True,
)
st.sidebar.divider()
st.sidebar.caption("WORKSPACE")
st.sidebar.caption("NAVIGATION")

NAVIGATION_ITEMS = [
    ("Overview", "▦"),
    ("Upload & Map Data", "⇧"),
    ("Demand Analytics", "⌁"),
    ("Inventory Optimization", "▣"),
    ("Forecast Comparison", "▤"),
    ("Demand Patterns", "◈"),
    ("Forecast Robustness", "◇"),
    ("Suppliers & Stock", "⇄"),
    ("Historical Records", "▤"),
]

if "main_navigation" not in st.session_state:
    st.session_state["main_navigation"] = "Overview"

for page, symbol in NAVIGATION_ITEMS:
    is_active = st.session_state["main_navigation"] == page
    if st.sidebar.button(
        f"{symbol}  {page}",
        key=f"nav_button_{page}",
        type="primary" if is_active else "secondary",
        use_container_width=True,
    ):
        if st.session_state["main_navigation"] != page:
            st.session_state["main_navigation"] = page
            st.rerun()

selected_page = st.session_state["main_navigation"]

# --------------------------------------------------
# ACTIVE DATASET STATUS AND QUICK SWITCH
# --------------------------------------------------
if "active_data" in st.session_state:
    st.sidebar.caption(
        f"ACTIVE DATASET · {st.session_state.get('active_data_source', 'Uploaded file')}"
    )
    st.sidebar.caption(
        f"{len(st.session_state['active_data']):,} validated rows"
    )
    if st.sidebar.button(
        "↩ Use Original Project Dataset",
        key="switch_to_original_dataset",
        use_container_width=True,
    ):
        for state_key in (
            "active_data",
            "active_data_source",
            "active_data_invalid_rows",
            "demand_products",
            "demand_warehouses",
        ):
            st.session_state.pop(state_key, None)
        st.rerun()
else:
    st.sidebar.caption("ACTIVE DATASET · Original project data")

# Keep the active dataset visible and allow a safe switch back from any page.
if "active_data" in st.session_state:
    st.sidebar.divider()
    st.sidebar.caption("ACTIVE DATASET")
    st.sidebar.write(st.session_state.get("active_data_source", "Uploaded dataset"))
    st.sidebar.caption(f"{len(st.session_state['active_data']):,} validated rows")
    if st.sidebar.button("↶ Use Original Project Dataset", key="sidebar_restore_original", use_container_width=True):
        for session_key in (
            "active_data",
            "active_data_source",
            "active_data_invalid_rows",
        ):
            st.session_state.pop(session_key, None)
        # Clear product/warehouse filter state so options from the upload do not linger.
        for session_key in ("demand_products", "demand_warehouses"):
            st.session_state.pop(session_key, None)
        st.rerun()

st.sidebar.markdown(
    """
    <div class="sidebar-footer">
        <div class="sidebar-status">● LOCAL DEMO MODE</div>
        <div style="margin-top: 5px;">
            Historical data · Inventory planning
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# DATA LOADING
# --------------------------------------------------
@st.cache_data
def load_data(path):
    return pd.read_csv(path, parse_dates=["Date"])


if not CLEANED_FILE.exists():
    try:
        from src.data_processing import load_and_clean_data

        with st.spinner("Preparing historical demand data..."):
            cleaned_data, quality_report = load_and_clean_data()

            CLEANED_FILE.parent.mkdir(parents=True, exist_ok=True)
            cleaned_data.to_csv(CLEANED_FILE, index=False)

    except Exception as exc:
        st.error("Unable to prepare historical demand data.")
        st.exception(exc)
        st.stop()

# Use a validated user-uploaded dataset for this browser session when available.
# The original cleaned CSV remains untouched and is the default data source.
if "active_data" in st.session_state:
    df = st.session_state["active_data"].copy()
else:
    df = load_data(str(CLEANED_FILE))

products = sorted(df["Product_Code"].dropna().unique().tolist())
warehouses = sorted(df["Warehouse"].dropna().unique().tolist())

# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------
st.title("📦 Supply Chain & Inventory Optimization")
st.markdown("Demand forecasting • Inventory planning • Data-driven decisions")
st.caption("Historical demand analytics, forecasting evaluation, and inventory planning.")

# --------------------------------------------------
# UPLOAD AND MAP USER DATA
# --------------------------------------------------
if selected_page == "Upload & Map Data":
    st.header("Upload & Map Your Data")
    st.caption(
        "Upload a CSV or Excel spreadsheet, preview its columns, and map them "
        "to the fields used by the platform. Your original project dataset is not overwritten."
    )

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Use a spreadsheet containing product, warehouse/location, date, and demand/quantity information.",
        key="custom_demand_upload",
    )

    if uploaded_file is not None:
        try:
            file_name = uploaded_file.name.lower()
            if file_name.endswith(".csv"):
                uploaded_df = pd.read_csv(uploaded_file)
            else:
                uploaded_df = pd.read_excel(uploaded_file)
        except Exception as error:
            st.error(
                "The file could not be read. For Excel files, make sure the workbook "
                "is valid and the required Excel reader is installed."
            )
            st.caption(f"Details: {error}")
            uploaded_df = None

        if uploaded_df is not None:
            uploaded_df.columns = [str(column).strip() for column in uploaded_df.columns]
            uploaded_df = uploaded_df.loc[:, ~uploaded_df.columns.duplicated()]

            if uploaded_df.empty or len(uploaded_df.columns) == 0:
                st.error("The uploaded file has no usable rows or columns.")
            else:
                st.subheader("1. Preview uploaded data")
                st.write(f"**Rows:** {len(uploaded_df):,} · **Columns:** {len(uploaded_df.columns):,}")
                st.dataframe(uploaded_df.head(10), use_container_width=True, hide_index=True)

                available_columns = uploaded_df.columns.tolist()
                no_mapping = "— Not provided —"

                def suggest_column(candidates):
                    normalized = {
                        str(column).strip().casefold().replace(" ", "_"): column
                        for column in available_columns
                    }
                    for candidate in candidates:
                        key = candidate.casefold().replace(" ", "_")
                        if key in normalized:
                            return normalized[key]
                    return available_columns[0]

                st.subheader("2. Map your spreadsheet columns")
                st.caption(
                    "Select which uploaded column represents each field. We suggest matches "
                    "automatically, but please verify them before applying."
                )

                with st.form("column_mapping_form"):
                    map_col1, map_col2 = st.columns(2)
                    with map_col1:
                        product_column = st.selectbox(
                            "Product / SKU",
                            options=available_columns,
                            index=available_columns.index(suggest_column([
                                "Product_Code", "Product Code", "Product", "SKU",
                                "Item", "Item_ID", "Product_ID"
                            ])),
                        )
                        warehouse_column = st.selectbox(
                            "Warehouse / Location",
                            options=available_columns,
                            index=available_columns.index(suggest_column([
                                "Warehouse", "Location", "Warehouse_ID", "Site",
                                "Store", "Distribution_Center"
                            ])),
                        )
                    with map_col2:
                        date_column = st.selectbox(
                            "Date",
                            options=available_columns,
                            index=available_columns.index(suggest_column([
                                "Date", "Order_Date", "Sales_Date", "Transaction_Date",
                                "Timestamp", "Day"
                            ])),
                        )
                        demand_column = st.selectbox(
                            "Demand / Quantity",
                            options=available_columns,
                            index=available_columns.index(suggest_column([
                                "Order_Demand", "Demand", "Quantity", "Quantity_Sold",
                                "Sales", "Units_Sold", "Order_Quantity", "Units"
                            ])),
                        )

                    category_options = [no_mapping] + available_columns
                    category_guess = next(
                        (
                            column for column in available_columns
                            if column.casefold().replace(" ", "_")
                            in {"product_category", "category", "product_type", "item_category"}
                        ),
                        no_mapping,
                    )
                    category_column = st.selectbox(
                        "Product category (optional)",
                        options=category_options,
                        index=category_options.index(category_guess),
                    )
                    apply_mapping = st.form_submit_button(
                        "Validate and Use This Dataset",
                        type="primary",
                        use_container_width=True,
                    )

                if apply_mapping:
                    required_mapping = {
                        "Product_Code": product_column,
                        "Warehouse": warehouse_column,
                        "Date": date_column,
                        "Order_Demand": demand_column,
                    }
                    if len(set(required_mapping.values())) != len(required_mapping):
                        st.error(
                            "Each required field must map to a different uploaded column. "
                            "Please correct the selections and try again."
                        )
                    else:
                        mapped_df = pd.DataFrame({
                            target: uploaded_df[source]
                            for target, source in required_mapping.items()
                        })
                        if category_column != no_mapping:
                            mapped_df["Product_Category"] = uploaded_df[category_column]
                        else:
                            mapped_df["Product_Category"] = "Uncategorized"

                        mapped_df["Date"] = pd.to_datetime(
                            mapped_df["Date"], errors="coerce"
                        )
                        mapped_df["Order_Demand"] = pd.to_numeric(
                            mapped_df["Order_Demand"].astype(str).str.replace(",", "", regex=False),
                            errors="coerce",
                        )
                        mapped_df["Product_Code"] = mapped_df["Product_Code"].astype("string").str.strip()
                        mapped_df["Warehouse"] = mapped_df["Warehouse"].astype("string").str.strip()
                        mapped_df["Product_Category"] = (
                            mapped_df["Product_Category"].fillna("Uncategorized").astype("string").str.strip()
                        )

                        invalid_mask = (
                            mapped_df["Product_Code"].isna()
                            | mapped_df["Product_Code"].eq("")
                            | mapped_df["Warehouse"].isna()
                            | mapped_df["Warehouse"].eq("")
                            | mapped_df["Date"].isna()
                            | mapped_df["Order_Demand"].isna()
                        )
                        invalid_count = int(invalid_mask.sum())
                        valid_df = mapped_df.loc[~invalid_mask].copy()

                        if valid_df.empty:
                            st.error(
                                "No valid rows remain after validation. Check the selected "
                                "columns and make sure dates and demand values are valid."
                            )
                        else:
                            valid_df["Year"] = valid_df["Date"].dt.year
                            valid_df["Month"] = valid_df["Date"].dt.month
                            valid_df["Day"] = valid_df["Date"].dt.day
                            valid_df["YearMonth"] = valid_df["Date"].dt.to_period("M").astype(str)
                            valid_df = valid_df.sort_values("Date").reset_index(drop=True)

                            # Report potential data-quality issues without silently deleting demand records.
                            duplicate_rows = int(valid_df.duplicated().sum())
                            negative_demand_rows = int((valid_df["Order_Demand"] < 0).sum())
                            if duplicate_rows:
                                st.warning(
                                    f"Data-quality notice: {duplicate_rows:,} exact duplicate row(s) remain in the dataset. "
                                    "Review them before using the results; they have not been removed automatically."
                                )
                            if negative_demand_rows:
                                st.warning(
                                    f"Data-quality notice: {negative_demand_rows:,} row(s) have negative demand. "
                                    "They are retained in the active dataset; inventory planning excludes negative demand."
                                )

                            st.session_state["active_data"] = valid_df
                            st.session_state["active_data_source"] = uploaded_file.name
                            st.session_state["active_data_invalid_rows"] = invalid_count
                            st.session_state["main_navigation"] = "Overview"
                            st.rerun()

    if "active_data" in st.session_state:
        st.divider()
        st.subheader("Current analysis dataset")
        st.success(
            f"Using uploaded file: {st.session_state.get('active_data_source', 'User dataset')}"
        )
        st.caption(
            f"{len(st.session_state['active_data']):,} valid rows are active for analysis. "
            "The original project CSV has not been changed."
        )
        invalid_rows = st.session_state.get("active_data_invalid_rows", 0)
        if invalid_rows:
            st.warning(
                f"{invalid_rows:,} row(s) were excluded because a required value was missing "
                "or the date/demand value could not be interpreted."
            )
        if st.button("Return to Original Project Dataset"):
            for state_key in (
                "active_data",
                "active_data_source",
                "active_data_invalid_rows",
                "demand_products",
                "demand_warehouses",
            ):
                st.session_state.pop(state_key, None)
            st.rerun()


# --------------------------------------------------
# OVERVIEW
# --------------------------------------------------
if selected_page == "Overview":
    st.header("Project Overview")
    st.caption(
        "A live view of your loaded historical dataset — "
        "demand trends, warehouse contribution, and product concentration."
    )


    total_demand = df["Order_Demand"].sum()

    col1, col2, col3, col4 = st.columns([1.5, 0.9, 1.1, 1.3])

    col1.metric("Total Demand", f"{total_demand:,.0f}")
    col2.metric("Products", f"{df['Product_Code'].nunique():,}")
    col3.metric("Warehouses", f"{df['Warehouse'].nunique():,}")
    col4.metric("Records", f"{len(df):,}")


    st.divider()
    daily_overview = (
        df.groupby("Date", as_index=False)["Order_Demand"]
        .sum()
        .sort_values("Date")
    )
    daily_overview["Date"] = pd.to_datetime(daily_overview["Date"])
    weekly_overview = (
        daily_overview.set_index("Date")["Order_Demand"]
        .resample("W")
        .sum()
        .rename("Weekly demand")
        .to_frame()
    )
    weekly_overview["7-week average"] = (
        weekly_overview["Weekly demand"].rolling(7, min_periods=1).mean()
    )


    # Independent chart/data controls for Overview

    st.subheader("Demand trend")
    st.caption(
        "Weekly recorded demand with a seven-week rolling average."
    )

    demand_trend_view = st.segmented_control(
        "Demand trend display",
        options=["Charts", "Data tables"],
        default="Charts",
        key="overview_demand_trend_view",
        label_visibility="collapsed",
    )

    if demand_trend_view == "Data tables":
        st.dataframe(
            weekly_overview.reset_index(),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.line_chart(weekly_overview, height=300)

    # Calculate warehouse and product demand
    left, right = st.columns(2)

    warehouse_overview = (
        df.groupby("Warehouse")["Order_Demand"]
        .sum()
        .sort_values(ascending=False)
    )

    product_overview = (
        df.groupby("Product_Code")["Order_Demand"]
        .sum()
        .sort_values(ascending=False)
        .head(10)
    )

    # Warehouse chart: independent switch
    with left:
        st.subheader("Warehouse demand")

        warehouse_view = st.segmented_control(
            "Warehouse display",
            options=["Charts", "Data tables"],
            default="Charts",
            key="overview_warehouse_view",
            label_visibility="collapsed",
        )

        if warehouse_view == "Data tables":
            st.dataframe(
                warehouse_overview.rename(
                    "Order_Demand"
                ).reset_index(),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.bar_chart(warehouse_overview, height=280)

    # Product chart: independent switch
    with right:
        st.subheader("Top 10 products")

        products_view = st.segmented_control(
            "Products display",
            options=["Charts", "Data tables"],
            default="Charts",
            key="overview_products_view",
            label_visibility="collapsed",
        )

        if products_view == "Data tables":
            st.dataframe(
                product_overview.rename(
                    "Order_Demand"
                ).reset_index(),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.bar_chart(product_overview, height=280)


    st.subheader("Explore the platform")

    feature_cards = [
        ("Demand Analytics", "Explore demand by product, warehouse, and date.", "⌁"),
        ("Inventory Optimization", "Plan safety stock, reorder points, and order quantities.", "▣"),
        ("Forecast Comparison", "Compare forecasting models and their accuracy.", "▤"),
        ("Demand Patterns", "Discover demand behaviour and product trends.", "◈"),
        ("Forecast Robustness", "Evaluate forecast errors and model stability.", "◇"),
        ("Suppliers & Stock", "Manage supplier offers and saved stock records.", "⇄"),
        ("Historical Records", "Browse and export historical demand data.", "▤"),
        ("Local demo", "Local data and demo inputs; no external API connected.", "●"),
    ]


    with st.container(key="overview_cards"):
        for offset in range(0, len(feature_cards), 3):
            feature_columns = st.columns(3)

            for column, (feature, description, symbol) in zip(
                feature_columns,
                feature_cards[offset:offset + 3],
            ):
                with column:
                    if feature == "Local demo":
                        st.markdown(
                            f"""
                            <div class="sc-feature-card">
                                <div class="sc-feature-heading">
                                    <span class="sc-feature-icon">{symbol}</span>
                                    <span>{feature}</span>
                                </div>
                                <div class="sc-feature-description">
                                    {description}
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        if st.button(
                            f"**{symbol}  {feature}**  \n{description}",                            use_container_width=True,
                        ):
                            st.session_state["main_navigation"] = feature
                            st.rerun()




# --------------------------------------------------
# DEMAND ANALYTICS
# --------------------------------------------------
if selected_page == "Demand Analytics":
    st.sidebar.divider()
    st.sidebar.subheader("Filters")

    selected_products = st.sidebar.multiselect(
        "Products",
        options=products,
        default=products[:10],
        key="demand_products",
    )
    selected_warehouses = st.sidebar.multiselect(
        "Warehouses",
        options=warehouses,
        default=warehouses,
        key="demand_warehouses",
    )

    filtered = df[
        df["Product_Code"].isin(selected_products)
        & df["Warehouse"].isin(selected_warehouses)
    ].copy()

    if filtered.empty:
        st.warning("No records match the selected filters.")
        st.stop()

    total_demand = filtered["Order_Demand"].sum()
    col1, col2, col3, col4 = st.columns([1.4, 1.1, 1, 1.3])
    col1.metric("Demand Units", f"{total_demand:,.0f}")
    col2.metric("Products", f"{filtered['Product_Code'].nunique():,}")
    col3.metric("Warehouses", f"{filtered['Warehouse'].nunique():,}")
    col4.metric("Records", f"{len(filtered):,}")


    # --------------------------------------------------
    # DAILY DEMAND — independent chart/data switch
    # --------------------------------------------------

    daily_demand = (
        filtered.groupby("Date", as_index=False)["Order_Demand"]
        .sum()
        .sort_values("Date")
    )

    st.subheader("Demand over time")

    daily_view = st.segmented_control(
        "Daily demand display",
        options=["Charts", "Data tables"],
        default="Charts",
        key="demand_daily_view",
        label_visibility="collapsed",
    )

    if daily_view == "Data tables":
        st.dataframe(
            daily_demand,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.line_chart(
            daily_demand.set_index("Date")["Order_Demand"],
            x_label="Date",
            y_label="Recorded order demand",
        )

    # --------------------------------------------------
    # WEEKLY DEMAND — independent chart/data switch
    # --------------------------------------------------
    weekly_demand = (
        daily_demand.set_index("Date")["Order_Demand"]
        .resample("W")
        .sum()
        .rename("Weekly demand")
    )

    st.subheader("Weekly demand — recorded vs smoothed")

    weekly_chart_data = pd.DataFrame({
        "Recorded weekly demand": weekly_demand,
        "7-week rolling average": weekly_demand.rolling(
            window=7, min_periods=1
        ).mean(),
    })

    weekly_view = st.segmented_control(
        "Weekly demand display",
        options=["Charts", "Data tables"],
        default="Charts",
        key="demand_weekly_view",
        label_visibility="collapsed",
    )

    if weekly_view == "Data tables":
        st.dataframe(
            weekly_chart_data.reset_index(),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.line_chart(
            weekly_chart_data,
            y_label="Weekly demand",
        )

    st.caption(
        "The daily chart preserves recorded daily totals. The weekly chart "
        "sums daily totals by calendar week. Neither chart removes extreme values."
    )

    # --------------------------------------------------
    # WAREHOUSE DEMAND — independent chart/data switch
    # --------------------------------------------------
    left, right = st.columns(2)

    with left:
        st.subheader("Demand by warehouse")

        warehouse_demand = (
            filtered.groupby("Warehouse")["Order_Demand"]
            .sum()
            .sort_values(ascending=False)
        )

        warehouse_view = st.segmented_control(
            "Warehouse demand display",
            options=["Charts", "Data tables"],
            default="Charts",
            key="demand_warehouse_view",
            label_visibility="collapsed",
        )

        if warehouse_view == "Data tables":
            st.dataframe(
                warehouse_demand.rename("Order_Demand").reset_index(),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.bar_chart(warehouse_demand)

    # --------------------------------------------------
    # TOP PRODUCTS — independent chart/data switch
    # --------------------------------------------------
    with right:
        st.subheader("Top 10 products by recorded demand")

        product_demand = (
            filtered.groupby("Product_Code")["Order_Demand"]
            .sum()
            .sort_values(ascending=False)
            .head(10)
        )

        products_view = st.segmented_control(
            "Top products display",
            options=["Charts", "Data tables"],
            default="Charts",
            key="demand_products_view",
            label_visibility="collapsed",
        )

        if products_view == "Data tables":
            st.dataframe(
                product_demand.rename("Order_Demand").reset_index(),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.bar_chart(product_demand)


# --------------------------------------------------
# INVENTORY OPTIMIZATION
# --------------------------------------------------
if selected_page == "Inventory Optimization":
    st.header("Inventory Optimization")
    st.caption(
        "Estimate reorder requirements using historical demand "
        "and inventory details supplied by the user."
    )

    available_pairs = (
        df[["Product_Code", "Warehouse"]]
        .drop_duplicates()
        .sort_values(["Product_Code", "Warehouse"])
    )

    inventory_col1, inventory_col2 = st.columns(2)
    with inventory_col1:
        inventory_product = st.selectbox(
            "Select product",
            options=sorted(available_pairs["Product_Code"].unique()),
            key="inventory_product",
        )

    valid_warehouses = sorted(
        available_pairs.loc[
            available_pairs["Product_Code"] == inventory_product,
            "Warehouse",
        ].unique()
    )
    with inventory_col2:
        inventory_warehouse = st.selectbox(
            "Select warehouse",
            options=valid_warehouses,
            key="inventory_warehouse",
        )

    stock_col, lead_col, review_col = st.columns(3)
    stock_widget_key = (
        f"inventory_current_stock_{inventory_product}_{inventory_warehouse}"
    )

    with stock_col:
        saved_inventory = get_stock(inventory_product, inventory_warehouse)
        if saved_inventory is not None:
            default_stock = int(saved_inventory["quantity"])
            st.caption(f"Using saved local stock: {default_stock:,} units")
        else:
            default_stock = 200
            st.caption("No saved stock found. Enter the current stock manually.")

        if stock_widget_key not in st.session_state:
            st.session_state[stock_widget_key] = default_stock

        current_stock = st.number_input(
            "Current available stock (units)",
            min_value=0,
            step=10,
            key=stock_widget_key,
        )

    with lead_col:
        lead_time_days = st.number_input(
            "Supplier lead time (days)", min_value=0, value=14, step=1
        )
    with review_col:
        review_period_days = st.number_input(
            "Review period (days)", min_value=1, value=7, step=1
        )

    if st.button("Calculate Inventory Policy", type="primary"):
        product_data = df[
            (df["Product_Code"] == inventory_product)
            & (df["Warehouse"] == inventory_warehouse)
        ].copy()

        if product_data.empty:
            st.warning(
                "No historical records exist for this product "
                "at the selected warehouse."
            )
        else:
            product_data["Planning_Demand"] = (
                product_data["Order_Demand"].clip(lower=0)
            )
            weekly = (
                product_data.groupby(pd.Grouper(key="Date", freq="W"))[
                    "Planning_Demand"
                ].sum()
            )

            if weekly.empty:
                st.warning("No weekly demand data is available.")
            else:
                full_weeks = pd.date_range(
                    start=weekly.index.min(),
                    end=weekly.index.max(),
                    freq="W",
                )
                weekly = weekly.reindex(full_weeks, fill_value=0)
                result = calculate_inventory_policy(
                    weekly_demand=weekly.tolist(),
                    current_stock=current_stock,
                    lead_time_days=lead_time_days,
                    review_period_days=review_period_days,
                )

                st.subheader("Inventory Recommendation")
                if result["reorder_needed"]:
                    st.warning(
                        "Replenishment is recommended based on the entered "
                        "stock and estimated demand."
                    )
                else:
                    st.success(
                        "Current stock is above the calculated reorder point."
                    )

                metric1, metric2, metric3 = st.columns(3)
                metric1.metric(
                    "Average Weekly Demand",
                    f'{result["average_weekly_demand"]:,.2f}',
                )
                metric2.metric(
                    "Safety Stock",
                    f'{result["safety_stock_units"]:,} units',
                )
                metric3.metric(
                    "Reorder Point",
                    f'{result["reorder_point_units"]:,} units',
                )

                metric4, metric5, metric6 = st.columns(3)
                metric4.metric(
                    "Target Stock", f'{result["target_stock_units"]:,} units'
                )
                metric5.metric(
                    "Current Stock", f'{result["current_stock_units"]:,} units'
                )
                metric6.metric(
                    "Suggested Order",
                    f'{result["suggested_order_quantity_units"]:,} units',
                )
                st.caption(
                    "Planning estimate only. Current stock and lead time are "
                    "user-entered; the dataset does not contain actual inventory "
                    "balances. Negative order adjustments are excluded from demand."
                )

# --------------------------------------------------
# FORECAST MODEL COMPARISON
# --------------------------------------------------
def evaluate_active_dataset_forecasts(source_df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """Evaluate simple forecasting baselines on active uploaded demand data.

    Each product-warehouse series uses a chronological holdout. At least eight
    calendar weeks are required so the test is not presented as meaningful for
    very short samples. XGBoost is not included in this lightweight evaluation;
    it remains available in the saved original-project experiment below.
    """
    records = source_df[["Product_Code", "Warehouse", "Date", "Order_Demand"]].copy()
    records["Date"] = pd.to_datetime(records["Date"], errors="coerce")
    records["Order_Demand"] = pd.to_numeric(records["Order_Demand"], errors="coerce")
    records = records.dropna(subset=["Product_Code", "Warehouse", "Date", "Order_Demand"])
    records["Order_Demand"] = records["Order_Demand"].clip(lower=0)

    pair_results = []
    short_pairs = 0
    eligible_pairs = 0
    for (product, warehouse), pair in records.groupby(["Product_Code", "Warehouse"]):
        weekly = (
            pair.set_index("Date")["Order_Demand"]
            .resample("W-SUN").sum()
            .sort_index()
        )
        if weekly.empty:
            continue
        full_index = pd.date_range(weekly.index.min(), weekly.index.max(), freq="W-SUN")
        weekly = weekly.reindex(full_index, fill_value=0).astype(float)
        if len(weekly) < 8:
            short_pairs += 1
            continue

        test_count = max(1, min(4, int(round(len(weekly) * 0.2))))
        train = weekly.iloc[:-test_count]
        actual = weekly.iloc[-test_count:].to_numpy(dtype=float)
        if train.empty:
            short_pairs += 1
            continue
        eligible_pairs += 1

        predictions = {
            "Historical_Mean": [float(train.mean())] * test_count,
            "Last_Week": [float(train.iloc[-1])] * test_count,
            "Moving_Average_4_Weeks": [float(train.tail(4).mean())] * test_count,
        }
        for method, values in predictions.items():
            predicted = pd.Series(values, dtype=float).clip(lower=0).to_numpy()
            errors = abs(actual - predicted)
            denominator = float(abs(actual).sum())
            wape = float(errors.sum() / denominator * 100) if denominator else float("nan")
            pair_results.append({
                "Product_Code": product,
                "Warehouse": warehouse,
                "Method": method,
                "Training_Weeks": len(train),
                "Testing_Weeks": test_count,
                "MAE": float(errors.mean()),
                "WAPE_percent": wape,
            })

    if not pair_results:
        return pd.DataFrame(), short_pairs, eligible_pairs

    pair_metrics = pd.DataFrame(pair_results)
    summary = (
        pair_metrics.groupby("Method", as_index=False)
        .agg(
            Pairs_Evaluated=("Product_Code", "count"),
            Mean_MAE=("MAE", "mean"),
            Median_MAE=("MAE", "median"),
            Mean_WAPE_percent=("WAPE_percent", "mean"),
            Median_WAPE_percent=("WAPE_percent", "median"),
        )
    )
    return summary, short_pairs, eligible_pairs


if selected_page == "Forecast Comparison":
    st.header("Forecast Model Comparison")
    if "active_data" in st.session_state:
        st.caption(
            "Evaluation uses the active uploaded dataset. Each product–warehouse pair "
            "is split chronologically; the most recent weeks are held out for testing. "
            "Lower MAE and WAPE generally indicate lower forecast error."
        )
        comparison, short_pairs, eligible_pairs = evaluate_active_dataset_forecasts(df)
        if comparison.empty:
            st.warning(
                "There is not enough history to evaluate forecasts from this upload. "
                "At least 8 calendar weeks per product–warehouse pair are required. "
                "Your uploaded file is still active; try a dataset with more history."
            )
            st.caption(f"Pairs skipped for short history: {short_pairs:,}")
        else:
            st.success(
                f"Evaluated {eligible_pairs:,} product–warehouse pair(s). "
                f"Skipped {short_pairs:,} pair(s) with fewer than 8 calendar weeks."
            )
            st.dataframe(comparison.round(2), width="stretch", hide_index=True)
            if "Method" in comparison.columns and "Mean_MAE" in comparison.columns:
                st.bar_chart(
                    comparison.set_index("Method")["Mean_MAE"],
                    x_label="Forecasting Method",
                    y_label="Mean MAE",
                )
            comparison_csv = comparison.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download Uploaded Dataset Forecast Comparison CSV",
                data=comparison_csv,
                file_name="uploaded_dataset_forecast_comparison.csv",
                mime="text/csv",
            )
            st.caption(
                "This upload evaluation compares three baseline methods. XGBoost and "
                "the saved robustness experiment remain part of the original project "
                "results and are not mixed into this upload-specific comparison."
            )
    elif COMPARISON_FILE.exists():
        comparison = pd.read_csv(COMPARISON_FILE)
        st.caption(
            "Saved results from the original project experiment. Lower MAE and WAPE "
            "generally indicate better forecasts. These results are not recalculated "
            "from an uploaded dataset."
        )
        st.dataframe(comparison, width="stretch", hide_index=True)
        if "Method" in comparison.columns and "Mean_MAE" in comparison.columns:
            st.bar_chart(
                comparison.set_index("Method")["Mean_MAE"],
                x_label="Forecasting Method",
                y_label="Mean MAE",
            )
        comparison_csv = comparison.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download Model Comparison CSV",
            data=comparison_csv,
            file_name="forecast_model_comparison.csv",
            mime="text/csv",
        )
    else:
        try:
            from src.forecasting import main as generate_forecast_comparison

            with st.spinner("Generating forecast model comparison..."):
                generate_forecast_comparison()

            if COMPARISON_FILE.exists():
                st.success("Forecast model comparison generated successfully.")
                st.rerun()
            else:
                st.error("Forecast comparison file was not created.")

        except Exception as exc:
            st.error("Unable to generate forecast model comparison.")
            st.exception(exc)

# --------------------------------------------------
# DEMAND PATTERN ANALYSIS
# --------------------------------------------------
def calculate_patterns_for_active_data(source_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate demand-pattern statistics from the currently active dataset."""
    records = source_df[["Product_Code", "Warehouse", "Date", "Order_Demand"]].copy()
    records["Date"] = pd.to_datetime(records["Date"], errors="coerce")
    records["Order_Demand"] = pd.to_numeric(records["Order_Demand"], errors="coerce")
    records = records.dropna(subset=["Product_Code", "Warehouse", "Date", "Order_Demand"])
    records["Order_Demand"] = records["Order_Demand"].clip(lower=0)

    columns = [
        "Product_Code", "Warehouse", "Demand_Pattern", "Weekly_Observations",
        "Weeks_With_Demand", "Nonzero_Week_Fraction", "Average_Weekly_Demand",
        "Demand_Std", "CV_Squared", "Average_Interval_Between_Demand_Weeks",
        "Maximum_Weekly_Demand",
    ]
    if records.empty:
        return pd.DataFrame(columns=columns)

    records["Week"] = records["Date"].dt.to_period("W").dt.start_time
    # Include weeks with zero demand between the first and last observed weeks.
    all_weeks = pd.date_range(records["Week"].min(), records["Week"].max(), freq="W-MON")
    global_week_count = len(all_weeks)
    rows = []

    for (product, warehouse), group in records.groupby(["Product_Code", "Warehouse"], dropna=False):
        weekly = group.groupby("Week")["Order_Demand"].sum().reindex(all_weeks, fill_value=0).astype(float)
        observations = int(len(weekly))
        nonzero = weekly[weekly > 0]
        weeks_with_demand = int(len(nonzero))
        nonzero_fraction = weeks_with_demand / observations if observations else 0.0
        average = float(weekly.mean()) if observations else 0.0
        std = float(weekly.std(ddof=1)) if observations > 1 else 0.0
        cv_squared = (std / average) ** 2 if average > 0 else 0.0
        demand_weeks = list(weekly.index[weekly > 0])
        if len(demand_weeks) > 1:
            interval = float(sum((b - a).days / 7 for a, b in zip(demand_weeks, demand_weeks[1:])) / (len(demand_weeks) - 1))
        else:
            interval = float(observations) if observations else 0.0

        # Avoid presenting a confident classification when there is too little history.
        if global_week_count < 8:
            pattern = "Insufficient History"
        elif nonzero_fraction >= 0.8:
            pattern = "Frequent" if cv_squared < 0.49 else "Variable Frequent"
        else:
            pattern = "Lumpy / Intermittent" if cv_squared < 0.49 else "Lumpy / Highly Intermittent"

        rows.append({
            "Product_Code": product,
            "Warehouse": warehouse,
            "Demand_Pattern": pattern,
            "Weekly_Observations": observations,
            "Weeks_With_Demand": weeks_with_demand,
            "Nonzero_Week_Fraction": round(nonzero_fraction, 4),
            "Average_Weekly_Demand": round(average, 2),
            "Demand_Std": round(std, 2),
            "CV_Squared": round(cv_squared, 4),
            "Average_Interval_Between_Demand_Weeks": round(interval, 2),
            "Maximum_Weekly_Demand": round(float(weekly.max()) if observations else 0.0, 2),
        })

    return pd.DataFrame(rows, columns=columns)


if selected_page == "Demand Patterns":
    st.header("Demand Pattern Analysis")
    is_uploaded_dataset = "active_data" in st.session_state

    if is_uploaded_dataset:
        pattern_df = calculate_patterns_for_active_data(df)
        st.caption(
            "Demand-pattern statistics are calculated from your active uploaded dataset. "
            "Classifications describe historical behavior, not guaranteed future demand."
        )
        if pattern_df.empty:
            st.warning("No valid product, warehouse, date, and demand records are available for pattern analysis.")
        else:
            weekly_observations = int(pattern_df["Weekly_Observations"].max())
            if weekly_observations < 8:
                st.warning(
                    f"This dataset covers only {weekly_observations} calendar week(s). "
                    "At least 8 weeks are required for a meaningful demand-pattern classification. "
                    "The table will show statistics from the uploaded data, but classifications are marked Insufficient History."
                )

            pattern_counts = (
                pattern_df["Demand_Pattern"].value_counts()
                .rename_axis("Demand Pattern")
                .reset_index(name="Product-Warehouse Pairs")
            )
            metric_cols = st.columns(3)
            metric_cols[0].metric("Product-Warehouse Pairs", f"{len(pattern_df):,}")
            metric_cols[1].metric("Demand Patterns", f"{pattern_df['Demand_Pattern'].nunique():,}")
            metric_cols[2].metric("Average Weekly Demand", f"{pattern_df['Average_Weekly_Demand'].mean():,.2f}")

            st.subheader("Demand Pattern Distribution")
            st.bar_chart(
                pattern_counts.set_index("Demand Pattern"),
                y="Product-Warehouse Pairs",
                x_label="Demand Pattern",
                y_label="Number of Product-Warehouse Pairs",
            )
            st.subheader("Demand Pattern Details")
            selected_pattern = st.selectbox(
                "Filter by demand pattern",
                options=["All"] + sorted(pattern_df["Demand_Pattern"].dropna().unique().tolist()),
                key="demand_pattern_filter_uploaded",
            )
            displayed_patterns = pattern_df if selected_pattern == "All" else pattern_df[pattern_df["Demand_Pattern"] == selected_pattern]
            st.dataframe(displayed_patterns, width="stretch", hide_index=True)
            st.download_button(
                "Download Demand Pattern Analysis CSV",
                data=displayed_patterns.to_csv(index=False).encode("utf-8"),
                file_name="uploaded_demand_pattern_analysis.csv",
                mime="text/csv",
            )
    elif PATTERN_FILE.exists():
        # Preserve the project's existing, precomputed analysis for the original dataset.
        pattern_df = pd.read_csv(PATTERN_FILE)
        st.caption(
            "Demand patterns are classified using historical weekly demand frequency and variability. "
            "These saved classifications describe historical behavior, not guaranteed future demand."
        )
        pattern_counts = (
            pattern_df["Demand_Pattern"].value_counts()
            .rename_axis("Demand Pattern")
            .reset_index(name="Product-Warehouse Pairs")
        )
        metric_cols = st.columns(3)
        metric_cols[0].metric("Product-Warehouse Pairs", f"{len(pattern_df):,}")
        metric_cols[1].metric("Demand Patterns", f"{pattern_df['Demand_Pattern'].nunique():,}")
        metric_cols[2].metric("Average Weekly Demand", f"{pattern_df['Average_Weekly_Demand'].mean():,.2f}")
        st.subheader("Demand Pattern Distribution")
        st.bar_chart(
            pattern_counts.set_index("Demand Pattern"),
            y="Product-Warehouse Pairs",
            x_label="Demand Pattern",
            y_label="Number of Product-Warehouse Pairs",
        )
        st.subheader("Demand Pattern Details")
        selected_pattern = st.selectbox(
            "Filter by demand pattern",
            options=["All"] + sorted(pattern_df["Demand_Pattern"].dropna().unique().tolist()),
            key="demand_pattern_filter_original",
        )

        displayed_patterns = pattern_df if selected_pattern == "All" else pattern_df[pattern_df["Demand_Pattern"] == selected_pattern]
        st.dataframe(displayed_patterns, width="stretch", hide_index=True)
        st.download_button(
            "Download Demand Pattern Analysis CSV",
            data=displayed_patterns.to_csv(index=False).encode("utf-8"),
            file_name="demand_pattern_analysis.csv",
            mime="text/csv",
        )
    else:
        try:
            from src.demand_analysis import analyze_demand_patterns

            with st.spinner("Generating demand pattern analysis..."):
                analyze_demand_patterns()

            if PATTERN_FILE.exists():
                st.success("Demand pattern analysis generated successfully.")
                st.rerun()
            else:
                st.error(
                    "Demand pattern analysis could not be generated. "
                    "Please check the application logs."
                )

        except Exception as exc:
            st.error("Unable to generate demand pattern analysis.")
            st.exception(exc)

# --------------------------------------------------
# FORECAST ROBUSTNESS COMPARISON
# --------------------------------------------------
def evaluate_active_dataset_robustness(source_df: pd.DataFrame):
    """Compare original XGBoost with a 95th-percentile-capped training variant."""
    try:
        from xgboost import XGBRegressor
    except Exception as exc:
        return pd.DataFrame(), 0, 0, f"XGBoost could not be loaded: {exc}"

    records = source_df[["Product_Code", "Warehouse", "Date", "Order_Demand"]].copy()
    records["Date"] = pd.to_datetime(records["Date"], errors="coerce")
    records["Order_Demand"] = pd.to_numeric(records["Order_Demand"], errors="coerce")
    records = records.dropna(subset=["Product_Code", "Warehouse", "Date", "Order_Demand"])
    records["Order_Demand"] = records["Order_Demand"].clip(lower=0)

    def make_features(values):
        values = list(map(float, values))
        return [
            values[-1],
            values[-2],
            values[-4],
            float(np.mean(values[-4:])),
            float(np.mean(values[-8:])),
        ]

    import numpy as np
    results = []
    short_pairs = 0
    evaluated_pairs = 0

    for (product, warehouse), pair in records.groupby(["Product_Code", "Warehouse"]):
        weekly = pair.set_index("Date")["Order_Demand"].resample("W-SUN").sum().sort_index()
        if weekly.empty:
            continue
        full_index = pd.date_range(weekly.index.min(), weekly.index.max(), freq="W-SUN")
        weekly = weekly.reindex(full_index, fill_value=0).astype(float).reset_index(drop=True)

        # Lag-based XGBoost requires more history than the baseline comparison.
        if len(weekly) < 20:
            short_pairs += 1
            continue

        test_count = max(1, min(4, int(round(len(weekly) * 0.2))))
        train_values = weekly.iloc[:-test_count].tolist()
        actual = weekly.iloc[-test_count:].to_numpy(dtype=float)

        # Build chronological supervised training rows from prior weeks only.
        x_train, y_train = [], []
        for target_idx in range(8, len(train_values)):
            x_train.append(make_features(train_values[:target_idx]))
            y_train.append(train_values[target_idx])

        if len(y_train) < 8:
            short_pairs += 1
            continue

        cap = float(np.quantile(np.asarray(y_train, dtype=float), 0.95))
        y_capped = np.minimum(np.asarray(y_train, dtype=float), cap)
        x_train = np.asarray(x_train, dtype=float)

        model_settings = dict(
            n_estimators=80,
            max_depth=3,
            learning_rate=0.05,
            objective="reg:squarederror",
            random_state=42,
            n_jobs=1,
            verbosity=0,
        )
        try:
            original_model = XGBRegressor(**model_settings)
            capped_model = XGBRegressor(**model_settings)
            original_model.fit(x_train, np.asarray(y_train, dtype=float))
            capped_model.fit(x_train, y_capped)
        except Exception as exc:
            return pd.DataFrame(), short_pairs, evaluated_pairs, f"XGBoost training failed: {exc}"

        histories = {
            "XGBoost_Original": list(map(float, train_values)),
            "XGBoost_Capped_Training": list(map(float, train_values)),
        }
        models = {
            "XGBoost_Original": original_model,
            "XGBoost_Capped_Training": capped_model,
        }
        for method, model in models.items():
            predictions = []
            history = histories[method]
            for _ in range(test_count):
                features = np.asarray([make_features(history)], dtype=float)
                prediction = max(0.0, float(model.predict(features)[0]))
                predictions.append(prediction)
                history.append(prediction)

            errors = np.abs(actual - np.asarray(predictions, dtype=float))
            denom = float(np.abs(actual).sum())
            wape = float(errors.sum() / denom * 100) if denom else float("nan")
            results.append({
                "Product_Code": product,
                "Warehouse": warehouse,
                "Method": method,
                "Training_Weeks": len(train_values),
                "Testing_Weeks": test_count,
                "Training_95th_Percentile_Cap": cap,
                "MAE": float(errors.mean()),
                "WAPE_percent": wape,
            })
        evaluated_pairs += 1

    return pd.DataFrame(results), short_pairs, evaluated_pairs, None


if selected_page == "Forecast Robustness":
    st.header("Forecast Robustness Comparison")
    if "active_data" in st.session_state:
        st.caption(
            "Upload-specific evaluation compares XGBoost trained on original weekly demand "
            "with XGBoost trained after capping training targets at the 95th percentile. "
            "The most recent weeks are held out chronologically."
        )
        with st.spinner("Evaluating XGBoost robustness for the active dataset..."):
            robustness_df, short_pairs, evaluated_pairs, error_message = (
                evaluate_active_dataset_robustness(df)
            )

        if error_message:
            st.error(error_message)
        elif robustness_df.empty:
            st.warning(
                "There is not enough history to evaluate XGBoost robustness from this upload. "
                "At least 20 calendar weeks per product–warehouse pair are required."
            )
        else:
            summary = (
                robustness_df.groupby("Method")
                .agg(
                    Pairs_Evaluated=("Product_Code", "count"),
                    Mean_MAE=("MAE", "mean"),
                    Median_MAE=("MAE", "median"),
                    Mean_WAPE_percent=("WAPE_percent", "mean"),
                    Median_WAPE_percent=("WAPE_percent", "median"),
                )
                .reset_index()
            )
            st.success(
                f"Evaluated {evaluated_pairs:,} product–warehouse pair(s). "
                f"Skipped {short_pairs:,} pair(s) with fewer than 20 calendar weeks."
            )
            st.subheader("Model Robustness Summary")
            st.dataframe(summary.round(2), width="stretch", hide_index=True)
            st.subheader("Mean MAE by Method")
            st.bar_chart(summary.set_index("Method")["Mean_MAE"],
                         x_label="Forecasting Method", y_label="Mean MAE")
            st.subheader("Mean WAPE by Method")
            st.bar_chart(summary.set_index("Method")["Mean_WAPE_percent"],
                         x_label="Forecasting Method", y_label="Mean WAPE (%)")
            st.subheader("Detailed Robustness Results")
            st.dataframe(robustness_df.round(2), width="stretch", hide_index=True)
            st.download_button(
                "Download Uploaded Dataset Robustness CSV",
                data=robustness_df.to_csv(index=False).encode("utf-8"),
                file_name="uploaded_dataset_forecast_robustness.csv",
                mime="text/csv",
            )
            st.caption(
                "Capping applies only to training targets. This is an experimental comparison; "
                "the capped model is not guaranteed to outperform the original model."
            )
    elif ROBUSTNESS_FILE.exists():
        robustness_df = pd.read_csv(ROBUSTNESS_FILE)
        st.caption(
            "Saved original-project experiment comparing original XGBoost with XGBoost "
            "trained using a 95th-percentile demand cap. These results are not recalculated "
            "from an uploaded dataset."
        )
        if not robustness_df.empty:
            robustness_summary = (
                robustness_df.groupby("Method")
                .agg(
                    Pairs_Evaluated=("Product_Code", "count"),
                    Mean_MAE=("MAE", "mean"),
                    Median_MAE=("MAE", "median"),
                    Mean_WAPE_percent=("WAPE_percent", "mean"),
                    Median_WAPE_percent=("WAPE_percent", "median"),
                )
                .reset_index()
            )
            st.subheader("Model Robustness Summary")
            st.dataframe(robustness_summary.round(2), width="stretch", hide_index=True)
            st.subheader("Mean MAE by Method")
            st.bar_chart(robustness_summary.set_index("Method")["Mean_MAE"],
                         x_label="Forecasting Method", y_label="Mean MAE")
            st.subheader("Mean WAPE by Method")
            st.bar_chart(robustness_summary.set_index("Method")["Mean_WAPE_percent"],
                         x_label="Forecasting Method", y_label="Mean WAPE (%)")
            st.subheader("Detailed Robustness Results")
            st.dataframe(robustness_df, width="stretch", hide_index=True)
            st.download_button(
                "Download Forecast Robustness CSV",
                data=robustness_df.to_csv(index=False).encode("utf-8"),
                file_name="forecast_robustness_comparison.csv",
                mime="text/csv",
            )
        else:
            st.warning("The forecast robustness file contains no records.")
    else:
        try:
            from src.forecast_robustness import main as generate_robustness_results

            with st.spinner("Generating forecast robustness results..."):
                generate_robustness_results()

            if ROBUSTNESS_FILE.exists():
                st.success("Forecast robustness results generated successfully.")
                st.rerun()
            else:
                st.error("Forecast robustness file was not created.")

        except Exception as exc:
            st.error("Unable to generate forecast robustness results.")
            st.exception(exc)

# --------------------------------------------------
# SUPPLIER MANAGEMENT & INVENTORY SNAPSHOTS
# --------------------------------------------------
if selected_page == "Suppliers & Stock":
    st.header("Supplier Management & Inventory Snapshots")
    st.info(
        "Current mode: Supabase cloud database. Supplier offers and "
        "inventory snapshots are stored in Supabase. Demand datasets "
        "and analysis outputs remain managed by the existing "
        "application workflow."
    )

    inventory_tab, supplier_tab = st.tabs(
        ["Inventory Snapshot", "Supplier Catalog"]
    )

    with inventory_tab:
        st.subheader("Record Available Stock")
        snapshot_product = st.selectbox(
            "Product", options=products, key="snapshot_product"
        )
        snapshot_warehouses = sorted(
            df.loc[
                df["Product_Code"] == snapshot_product, "Warehouse"
            ].dropna().unique().tolist()
        )
        snapshot_warehouse = st.selectbox(
            "Warehouse",
            options=snapshot_warehouses,
            key="snapshot_warehouse",
        )
        saved_stock = get_stock(snapshot_product, snapshot_warehouse)

        if saved_stock:
            st.caption(
                f"Saved local quantity: {saved_stock['quantity']:,} units. "
                f"Last updated: {saved_stock['updated_at']}"
            )
        else:
            st.caption("No saved stock snapshot exists for this selection.")

        snapshot_quantity = st.number_input(
            "Actual stock quantity to save",
            min_value=0,
            value=int(saved_stock["quantity"]) if saved_stock else 0,
            step=1,
            key="snapshot_quantity",
        )
        if st.button("Save Local Stock Snapshot"):
            update_inventory(
                snapshot_product, snapshot_warehouse, snapshot_quantity
            )
            st.success(
                "Local stock snapshot saved. This was not synchronized "
                "with an external system."
            )
            st.rerun()

        snapshot = get_inventory_snapshot()
        if snapshot["items"]:
            st.subheader("Saved Inventory Records")
            st.dataframe(
                pd.DataFrame(snapshot["items"]),
                width="stretch",
                hide_index=True,
            )
        else:
            st.caption("No stock records have been saved yet.")

    with supplier_tab:
        st.subheader("Add Supplier Offer")
        with st.form("supplier_offer_form", clear_on_submit=True):
            supplier_name = st.text_input("Supplier name")
            supplier_product = st.selectbox(
                "Product offered", options=products, key="supplier_product"
            )
            supplier_price = st.number_input(
                "Unit price", min_value=0.0, value=1.0, step=0.5
            )
            supplier_lead_time = st.number_input(
                "Lead time (days)", min_value=0, value=7, step=1
            )
            supplier_moq = st.number_input(
                "Minimum order quantity", min_value=1, value=1, step=1
            )
            submitted = st.form_submit_button("Save Supplier Offer")

        if submitted:
            if not supplier_name.strip():
                st.error("Enter a supplier name.")
            else:
                offers = get_suppliers()
                new_offer = {
                    "supplier_name": supplier_name.strip(),
                    "product_code": supplier_product,
                    "unit_price": float(supplier_price),
                    "lead_time_days": int(supplier_lead_time),
                    "minimum_order_quantity": int(supplier_moq),
                    "source": "MANUAL_DEMO",
                    "updated_at": pd.Timestamp.now(tz="UTC").isoformat(),
                }
                duplicate_exists = any(
                    offer.get("supplier_name", "").strip().casefold()
                    == new_offer["supplier_name"].casefold()
                    and offer.get("product_code") == new_offer["product_code"]
                    and offer.get("unit_price") == new_offer["unit_price"]
                    and offer.get("lead_time_days")
                    == new_offer["lead_time_days"]
                    and offer.get("minimum_order_quantity")
                    == new_offer["minimum_order_quantity"]
                    for offer in offers
                )
                if duplicate_exists:
                    st.warning(
                        "This exact supplier offer already exists. "
                        "No duplicate was saved."
                    )
                else:
                    offers.append(new_offer)
                    try:
                        save_suppliers(offers)
                        st.success("Supplier offer saved locally.")
                        st.rerun()
                    except ValueError as error:
                        st.error(str(error))

        st.subheader("Compare Supplier Offers")
        compare_product = st.selectbox(
            "Product to compare",
            options=products,
            key="compare_supplier_product",
        )
        supplier_comparison = compare_suppliers(compare_product)
        if supplier_comparison.empty:
            st.info("No supplier offers saved for this product yet.")
        else:
            st.dataframe(
                supplier_comparison,
                width="stretch",
                hide_index=True,
            )
            st.caption(
                "Offers are sorted by unit price, then lead time. Prices and "
                "lead times are manually entered demo data, not verified quotations."
            )

# --------------------------------------------------
# HISTORICAL RECORDS
# --------------------------------------------------
if selected_page == "Historical Records":
    st.header("Historical Demand Records")
    st.caption(
        "Browse the most recent 500 records in the cleaned historical dataset."
    )
    historical_records = df[
        [
            "Product_Code",
            "Warehouse",
            "Product_Category",
            "Date",
            "Order_Demand",
        ]
    ].sort_values("Date", ascending=False).head(500)
    st.dataframe(
        historical_records,
        width="stretch",
        hide_index=True,
    )
    st.download_button(
        "Download Historical Records CSV",
        data=historical_records.to_csv(index=False).encode("utf-8"),
        file_name="historical_demand_records.csv",
        mime="text/csv",
    )
