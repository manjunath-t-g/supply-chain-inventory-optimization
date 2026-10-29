
from datetime import datetime, timezone
from pathlib import Path
import json

import pandas as pd
import streamlit as st
from supabase import create_client


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INTEGRATION_DIR = PROJECT_ROOT / "data" / "integrations"
INVENTORY_FILE = INTEGRATION_DIR / "inventory_snapshot.json"
SUPPLIERS_FILE = INTEGRATION_DIR / "suppliers.json"


def current_timestamp():
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat()


@st.cache_resource
def _get_supabase_client():
    """Create and cache the server-side Supabase client."""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except Exception as exc:
        raise RuntimeError(
            "Supabase configuration is missing. "
            "Check .streamlit/secrets.toml."
        ) from exc

    if not url or not key:
        raise RuntimeError("Supabase URL or key is empty.")

    return create_client(url, key)


def load_json(path, default):
    """Load local integration data, or return a default."""
    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path, data):
    """Save local integration data."""
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def get_inventory_snapshot():
    """Return the current inventory snapshot from Supabase."""
    response = (
        _get_supabase_client()
        .table("inventory")
        .select(
            "product_code, warehouse, quantity, updated_at, source"
        )
        .not_.is_("product_code", "null")
        .not_.is_("warehouse", "null")
        .order("id")
        .execute()
    )

    items = response.data or []

    latest = max(
        items,
        key=lambda item: item.get("updated_at") or "",
        default=None,
    )

    return {
        "source": latest.get("source", "SUPABASE")
        if latest else "SUPABASE",
        "updated_at": latest.get("updated_at")
        if latest else None,
        "items": items,
    }


def update_inventory(product_code, warehouse, quantity):
    """Save a stock quantity in Supabase."""
    if (
        not isinstance(product_code, str)
        or not product_code.strip()
        or not isinstance(warehouse, str)
        or not warehouse.strip()
    ):
        raise ValueError("Product and warehouse are required.")

    if (
        isinstance(quantity, bool)
        or not isinstance(quantity, (int, float))
    ):
        raise ValueError("Stock quantity must be numeric.")

    if quantity < 0 or not float(quantity).is_integer():
        raise ValueError(
            "Stock quantity must be a non-negative whole number."
        )

    product_code = product_code.strip()
    warehouse = warehouse.strip()
    quantity = int(quantity)
    timestamp = current_timestamp()
    client = _get_supabase_client()

    existing = (
        client.table("inventory")
        .select("id")
        .eq("product_code", product_code)
        .eq("warehouse", warehouse)
        .limit(1)
        .execute()
    )

    record = {
        "product_code": product_code,
        "product_name": product_code,
        "warehouse": warehouse,
        "quantity": quantity,
        "stock_quantity": quantity,
        "source": "MANUAL_SUPABASE_UPDATE",
        "updated_at": timestamp,
    }

    if existing.data:
        result = (
            client.table("inventory")
            .update(record)
            .eq("id", existing.data[0]["id"])
            .execute()
        )
    else:
        result = (
            client.table("inventory")
            .insert(record)
            .execute()
        )

    if not result.data:
        raise RuntimeError("Supabase did not confirm the inventory update.")

    return {
        "product_code": product_code,
        "warehouse": warehouse,
        "quantity": quantity,
        "updated_at": timestamp,
    }


def get_stock(product_code, warehouse):
    """Find saved stock for a product and warehouse."""
    response = (
        _get_supabase_client()
        .table("inventory")
        .select(
            "product_code, warehouse, quantity, updated_at, source"
        )
        .eq("product_code", product_code)
        .eq("warehouse", warehouse)
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


def get_suppliers():
    """Return the supplier catalog from Supabase."""
    response = (
        _get_supabase_client()
        .table("suppliers")
        .select(
            "supplier_name, product_code, unit_price, "
            "lead_time_days, minimum_order_quantity, "
            "source, updated_at"
        )
        .order("id")
        .execute()
    )

    return response.data or []


def save_suppliers(suppliers):
    """Validate and atomically replace the supplier catalog."""
    if not isinstance(suppliers, list):
        raise ValueError("Suppliers must be provided as a list.")

    normalized = []

    for supplier in suppliers:
        if not supplier.get("supplier_name"):
            raise ValueError("Every supplier needs a name.")

        if not supplier.get("product_code"):
            raise ValueError("Every supplier needs a product code.")

        price = supplier.get("unit_price")

        if (
            isinstance(price, bool)
            or not isinstance(price, (int, float))
            or price < 0
        ):
            raise ValueError("Unit price must be non-negative.")

        lead_time = supplier.get("lead_time_days")

        if (
            isinstance(lead_time, bool)
            or not isinstance(lead_time, int)
            or lead_time < 0
        ):
            raise ValueError(
                "Lead time must be a non-negative whole number."
            )

        minimum_order = supplier.get("minimum_order_quantity", 1)

        if (
            isinstance(minimum_order, bool)
            or not isinstance(minimum_order, int)
            or minimum_order < 1
        ):
            raise ValueError(
                "Minimum order quantity must be at least one."
            )

        normalized.append({
            "supplier_name": supplier["supplier_name"],
            "product_code": supplier["product_code"],
            "unit_price": price,
            "lead_time_days": lead_time,
            "minimum_order_quantity": minimum_order,
            "source": supplier.get("source", "MANUAL_SUPABASE"),
            "updated_at": supplier.get("updated_at") or current_timestamp(),
        })

    result = (
        _get_supabase_client()
        .rpc(
            "replace_suppliers",
            {"supplier_rows": normalized},
        )
        .execute()
    )

    return result.data


def compare_suppliers(product_code):
    """Compare suppliers for one product by price and lead time."""
    suppliers = get_suppliers()

    matches = [
        supplier for supplier in suppliers
        if supplier.get("product_code") == product_code
    ]

    if not matches:
        return pd.DataFrame()

    return (
        pd.DataFrame(matches)
        .sort_values(
            ["unit_price", "lead_time_days"],
            ascending=[True, True],
        )
        .reset_index(drop=True)
    )


if __name__ == "__main__":
    print("=== SUPPLY CHAIN INTEGRATION STATUS ===")
    print("Inventory source: Supabase PostgreSQL")
    print("Supplier source: Supabase PostgreSQL")

    snapshot = get_inventory_snapshot()
    print("Inventory records:", len(snapshot["items"]))
    print("Last snapshot update:", snapshot["updated_at"])
    print("Supplier records:", len(get_suppliers()))
