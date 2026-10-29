
import json
from pathlib import Path

import streamlit as st
from supabase import create_client


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "integrations"


def main():
    client = create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"],
    )

    with (DATA_DIR / "suppliers.json").open(
        encoding="utf-8"
    ) as file:
        suppliers = json.load(file)

    with (DATA_DIR / "inventory_snapshot.json").open(
        encoding="utf-8"
    ) as file:
        snapshot = json.load(file)

    inventory = snapshot.get("items", [])

    if not isinstance(suppliers, list) or not isinstance(inventory, list):
        raise ValueError("Unexpected JSON structure.")

    for supplier in suppliers:
        if (
            not supplier.get("supplier_name")
            or not supplier.get("product_code")
            or isinstance(supplier.get("unit_price"), bool)
            or not isinstance(supplier.get("unit_price"), (int, float))
            or supplier["unit_price"] < 0
            or isinstance(supplier.get("lead_time_days"), bool)
            or not isinstance(supplier.get("lead_time_days"), int)
            or supplier["lead_time_days"] < 0
            or isinstance(
                supplier.get("minimum_order_quantity", 1), bool
            )
            or not isinstance(
                supplier.get("minimum_order_quantity", 1), int
            )
            or supplier.get("minimum_order_quantity", 1) < 1
        ):
            raise ValueError("Invalid supplier record; migration stopped.")

    for item in inventory:
        if (
            not item.get("product_code")
            or not item.get("warehouse")
            or isinstance(item.get("quantity"), bool)
            or not isinstance(item.get("quantity"), int)
            or item["quantity"] < 0
        ):
            raise ValueError("Invalid inventory record; migration stopped.")

    # Check both tables before making any changes.
    existing_suppliers = (
        client.table("suppliers").select("id").execute().data or []
    )
    existing_inventory = (
        client.table("inventory")
        .select("id")
        .not_.is_("product_code", "null")
        .not_.is_("warehouse", "null")
        .execute().data or []
    )

    if existing_suppliers or existing_inventory:
        raise RuntimeError(
            "Migration stopped safely because the target tables "
            "already contain records. No records were inserted. "
            "Inspect the tables before deciding how to proceed."
        )

    supplier_rows = [
        {
            "supplier_name": item["supplier_name"],
            "product_code": item["product_code"],
            "unit_price": item["unit_price"],
            "lead_time_days": item["lead_time_days"],
            "minimum_order_quantity": item.get(
                "minimum_order_quantity", 1
            ),
            "source": item.get("source", "JSON_MIGRATION"),
            "updated_at": item.get("updated_at"),
        }
        for item in suppliers
    ]

    inventory_rows = [
        {
            "product_name": item["product_code"],
            "product_code": item["product_code"],
            "warehouse": item["warehouse"],
            "quantity": item["quantity"],
            "stock_quantity": item["quantity"],
            "source": snapshot.get("source", "JSON_MIGRATION"),
            "updated_at": item.get("updated_at"),
        }
        for item in inventory
    ]

    # Each table is inserted in one bulk request.
    if supplier_rows:
        client.table("suppliers").insert(supplier_rows).execute()

    if inventory_rows:
        client.table("inventory").insert(inventory_rows).execute()

    print("Migration requests completed.")
    print("Supplier records migrated:", len(supplier_rows))
    print("Inventory records migrated:", len(inventory_rows))
    print("Local JSON files were not modified.")
    print("Verify both counts in Supabase Table Editor.")


if __name__ == "__main__":
    main()
