"""
RetailFlow - End-to-End Medallion Lakehouse Ingestion Pipeline
Processes: Raw (CSV) -> Bronze (Parquet) -> Silver (Cleaned) -> Gold (Aggregated & Business Ready)
Also exports CSVs for Power BI ingestion.
"""

from pathlib import Path
import re
import pandas as pd


def get_project_root() -> Path:
    """Find the RetailFlow root directory reliably regardless of execution context."""
    current = Path.cwd()
    for candidate in [current, current / "RetailFlow", *current.parents]:
        if (candidate / "data" / "raw").exists():
            return candidate
        if (candidate / "RetailFlow" / "data" / "raw").exists():
            return candidate / "RetailFlow"
    # Fallback to this file's grandparent directory
    file_root = Path(__file__).resolve().parent.parent
    if (file_root / "data" / "raw").exists():
        return file_root
    raise FileNotFoundError("Could not locate RetailFlow project root with data/raw directory.")


def run_bronze_layer(root: Path):
    """Ingest raw CSV files into bronze Parquet format."""
    print("\n--- Running Bronze Layer ---")
    raw_path = root / "data" / "raw"
    bronze_path = root / "data" / "bronze"
    bronze_path.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(raw_path.glob("*.csv"))
    if not raw_files:
        raise FileNotFoundError(f"No CSV files found in {raw_path}")

    summary = []
    for file in raw_files:
        df = pd.read_csv(file)
        out_name = file.stem + ".parquet"
        out_file = bronze_path / out_name
        df.to_parquet(out_file, index=False)
        summary.append({"dataset": file.name, "rows": len(df), "columns": len(df.columns)})
        print(f"  [Bronze] Ingested {file.name} -> {out_name} ({len(df):,} rows)")

    print(f"Bronze layer completed successfully! Total datasets: {len(summary)}")
    return summary


def run_silver_layer(root: Path):
    """Clean, standardize, and deduplicate bronze datasets into silver layer."""
    print("\n--- Running Silver Layer ---")
    bronze_path = root / "data" / "bronze"
    silver_path = root / "data" / "silver"
    silver_path.mkdir(parents=True, exist_ok=True)

    bronze_files = sorted(bronze_path.glob("*.parquet"))
    if not bronze_files:
        raise FileNotFoundError(f"No Bronze parquet files found in {bronze_path}")

    summary = []
    for file in bronze_files:
        df = pd.read_parquet(file)
        original_rows = len(df)

        # Standardize column names
        df.columns = [
            re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9]+", "_", str(col).strip())).strip("_").lower()
            for col in df.columns
        ]

        # Drop entirely null rows
        df = df.dropna(how="all")

        # Trim text strings and convert empty strings to NA
        for col in df.select_dtypes(include=["object", "string"]).columns:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            df[col] = df[col].replace("", pd.NA)

        # Drop duplicate records
        df = df.drop_duplicates()

        out_file = silver_path / file.name
        df.to_parquet(out_file, index=False)
        cleaned_rows = len(df)
        removed = original_rows - cleaned_rows
        summary.append({
            "dataset": file.name,
            "original_rows": original_rows,
            "cleaned_rows": cleaned_rows,
            "removed": removed
        })
        print(f"  [Silver] Cleaned {file.name} -> {cleaned_rows:,} rows (removed {removed:,} duplicates/empty)")

    print(f"Silver layer completed successfully! Total datasets: {len(summary)}")
    return summary


def run_gold_layer(root: Path):
    """Generate business-ready Gold analytical tables and export for Power BI."""
    print("\n--- Running Gold Layer ---")
    silver_path = root / "data" / "silver"
    gold_path = root / "data" / "gold"
    powerbi_data_path = root / "powerbi" / "data"

    gold_path.mkdir(parents=True, exist_ok=True)
    powerbi_data_path.mkdir(parents=True, exist_ok=True)

    # Load all silver datasets
    data = {}
    for file in silver_path.glob("*.parquet"):
        name = file.stem.replace("_dataset", "")
        data[name] = pd.read_parquet(file)

    orders = data["olist_orders"].copy()
    customers = data["olist_customers"].copy()
    payments = data["olist_order_payments"].copy()
    items = data.get("olist_order_items")
    products = data.get("olist_products")
    categories = data.get("product_category_name_translation")

    # 1. Order Items Summary
    if items is not None:
        item_summary = items.groupby("order_id").agg(
            total_items=("order_item_id", "count"),
            product_revenue=("price", "sum"),
            shipping_cost=("freight_value", "sum")
        ).reset_index()
    else:
        item_summary = pd.DataFrame(columns=["order_id", "total_items", "product_revenue", "shipping_cost"])

    # 2. Payments Summary
    payment_summary = payments.groupby("order_id").agg(
        payment_total=("payment_value", "sum"),
        primary_payment_type=("payment_type", "first"),
        total_payment_installments=("payment_installments", "max")
    ).reset_index()

    # Merge into gold_order_summary
    gold_order_summary = orders.merge(item_summary, on="order_id", how="left")
    gold_order_summary = gold_order_summary.merge(payment_summary, on="order_id", how="left")
    gold_order_summary = gold_order_summary.merge(
        customers[["customer_id", "customer_unique_id", "customer_city", "customer_state"]],
        on="customer_id", how="left"
    )

    gold_order_summary["payment_total"] = gold_order_summary["payment_total"].fillna(0.0)
    # If items was missing, fallback smoothly to payment_total
    if items is not None:
        gold_order_summary["total_items"] = gold_order_summary["total_items"].fillna(1)
        gold_order_summary["product_revenue"] = gold_order_summary["product_revenue"].fillna(
            gold_order_summary["payment_total"] * 0.85
        )
        gold_order_summary["shipping_cost"] = gold_order_summary["shipping_cost"].fillna(
            gold_order_summary["payment_total"] * 0.15
        )
    else:
        gold_order_summary["total_items"] = 1
        gold_order_summary["product_revenue"] = gold_order_summary["payment_total"] * 0.85
        gold_order_summary["shipping_cost"] = gold_order_summary["payment_total"] * 0.15

    # Parse timestamps and calculate delivery performance
    for col in ["order_purchase_timestamp", "order_approved_at", "order_delivered_customer_date", "order_estimated_delivery_date"]:
        gold_order_summary[col] = pd.to_datetime(gold_order_summary[col], errors="coerce")

    gold_order_summary["delivery_days"] = (
        gold_order_summary["order_delivered_customer_date"] - gold_order_summary["order_purchase_timestamp"]
    ).dt.total_seconds() / (24 * 3600)

    gold_order_summary["is_delayed"] = (
        gold_order_summary["order_delivered_customer_date"] > gold_order_summary["order_estimated_delivery_date"]
    ).astype("Int64")

    # Filter delivered orders for sales analysis
    delivered = gold_order_summary[gold_order_summary["order_status"] == "delivered"].copy()
    delivered["sales_month"] = delivered["order_purchase_timestamp"].dt.to_period("M").astype(str)

    # 3. Monthly Sales
    gold_monthly_sales = delivered.groupby("sales_month").agg(
        total_orders=("order_id", "nunique"),
        total_customers=("customer_unique_id", "nunique"),
        total_revenue=("product_revenue", "sum"),
        total_shipping=("shipping_cost", "sum"),
        total_payment=("payment_total", "sum"),
        avg_order_value=("payment_total", "mean")
    ).reset_index()
    gold_monthly_sales["total_revenue"] = gold_monthly_sales["total_revenue"].round(2)
    gold_monthly_sales["total_shipping"] = gold_monthly_sales["total_shipping"].round(2)
    gold_monthly_sales["total_payment"] = gold_monthly_sales["total_payment"].round(2)
    gold_monthly_sales["avg_order_value"] = gold_monthly_sales["avg_order_value"].round(2)

    # 4. State Sales
    gold_state_sales = delivered.groupby("customer_state").agg(
        total_orders=("order_id", "nunique"),
        total_customers=("customer_unique_id", "nunique"),
        total_revenue=("product_revenue", "sum"),
        total_shipping=("shipping_cost", "sum"),
        total_payment=("payment_total", "sum"),
        avg_order_value=("payment_total", "mean")
    ).reset_index()
    gold_state_sales["total_revenue"] = gold_state_sales["total_revenue"].round(2)
    gold_state_sales["total_payment"] = gold_state_sales["total_payment"].round(2)
    gold_state_sales["avg_order_value"] = gold_state_sales["avg_order_value"].round(2)
    gold_state_sales = gold_state_sales.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)

    # 5. Category Sales
    if items is not None and products is not None:
        cat_df = items.merge(orders[["order_id", "order_status"]], on="order_id", how="inner")
        cat_df = cat_df[cat_df["order_status"] == "delivered"]
        cat_df = cat_df.merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
        if categories is not None:
            cat_df = cat_df.merge(categories, on="product_category_name", how="left")
            cat_df["category"] = cat_df["product_category_name_english"].fillna(cat_df["product_category_name"]).fillna("other")
        else:
            cat_df["category"] = cat_df["product_category_name"].fillna("other")

        gold_category_sales = cat_df.groupby("category").agg(
            total_items_sold=("order_item_id", "count"),
            total_orders=("order_id", "nunique"),
            total_revenue=("price", "sum"),
            avg_item_price=("price", "mean")
        ).reset_index().rename(columns={"category": "product_category_name_english"})
        gold_category_sales["total_revenue"] = gold_category_sales["total_revenue"].round(2)
        gold_category_sales["avg_item_price"] = gold_category_sales["avg_item_price"].round(2)
        gold_category_sales = gold_category_sales.sort_values(by="total_revenue", ascending=False).reset_index(drop=True)
    else:
        gold_category_sales = pd.DataFrame(columns=[
            "product_category_name_english", "total_items_sold", "total_orders", "total_revenue", "avg_item_price"
        ])

    # 6. Payment Analysis
    pay_orders = payments.merge(orders[["order_id", "order_status"]], on="order_id", how="inner")
    pay_delivered = pay_orders[pay_orders["order_status"] == "delivered"]
    gold_payment_analysis = pay_delivered.groupby("payment_type").agg(
        total_transactions=("order_id", "count"),
        total_orders=("order_id", "nunique"),
        total_payment_value=("payment_value", "sum"),
        avg_transaction_value=("payment_value", "mean")
    ).reset_index()
    gold_payment_analysis["total_payment_value"] = gold_payment_analysis["total_payment_value"].round(2)
    gold_payment_analysis["avg_transaction_value"] = gold_payment_analysis["avg_transaction_value"].round(2)
    gold_payment_analysis = gold_payment_analysis.sort_values(by="total_payment_value", ascending=False).reset_index(drop=True)

    gold_tables = {
        "gold_order_summary": gold_order_summary,
        "gold_monthly_sales": gold_monthly_sales,
        "gold_category_sales": gold_category_sales,
        "gold_state_sales": gold_state_sales,
        "gold_payment_analysis": gold_payment_analysis
    }

    print("\nSaving Gold Tables (Parquet + CSV):")
    for name, df in gold_tables.items():
        pq_path = gold_path / f"{name}.parquet"
        csv_path = gold_path / f"{name}.csv"
        pbi_csv = powerbi_data_path / f"{name}.csv"

        df.to_parquet(pq_path, index=False)
        df.to_csv(csv_path, index=False)
        df.to_csv(pbi_csv, index=False)
        print(f"  [Gold] Saved {name} ({len(df):,} rows) -> Parquet & CSV")

    print("\nGold layer completed successfully!")
    return gold_tables


def main():
    root = get_project_root()
    print("=" * 60)
    print(f"RetailFlow Medallion Lakehouse Pipeline")
    print(f"Project Root: {root}")
    print("=" * 60)
    run_bronze_layer(root)
    run_silver_layer(root)
    run_gold_layer(root)
    print("\nALL LAYERS COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
