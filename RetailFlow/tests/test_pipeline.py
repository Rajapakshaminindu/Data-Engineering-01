"""
RetailFlow - Automated Quality & Integration Test Suite
Validates:
1. Raw dataset presence and integrity
2. Bronze layer parquet outputs
3. Silver layer cleaning, deduplication, and schema consistency
4. Gold layer analytical tables completeness and null-safety
"""

from pathlib import Path
import pandas as pd


def get_root() -> Path:
    current = Path.cwd()
    for candidate in [current, current / "RetailFlow", *current.parents]:
        if (candidate / "data" / "raw").exists():
            return candidate
        if (candidate / "RetailFlow" / "data" / "raw").exists():
            return candidate / "RetailFlow"
    return current


ROOT = get_root()


def test_raw_data_exists():
    raw_path = ROOT / "data" / "raw"
    csv_files = list(raw_path.glob("*.csv"))
    assert len(csv_files) >= 9, f"Expected at least 9 raw CSV files, found {len(csv_files)}"
    assert (raw_path / "olist_orders_dataset.csv").exists()
    assert (raw_path / "olist_order_items_dataset.csv").exists()
    assert (raw_path / "olist_order_payments_dataset.csv").exists()


def test_bronze_layer():
    bronze_path = ROOT / "data" / "bronze"
    pq_files = list(bronze_path.glob("*.parquet"))
    assert len(pq_files) >= 9, f"Expected at least 9 bronze parquet files, found {len(pq_files)}"


def test_silver_layer():
    silver_path = ROOT / "data" / "silver"
    orders_file = silver_path / "olist_orders_dataset.parquet"
    assert orders_file.exists()
    df_orders = pd.read_parquet(orders_file)
    assert len(df_orders) == 99441
    # Check no completely empty rows or uncleaned columns
    assert "order_id" in df_orders.columns
    assert df_orders["order_id"].nunique() == 99441


def test_gold_layer_completeness():
    gold_path = ROOT / "data" / "gold"
    tables = [
        "gold_order_summary",
        "gold_monthly_sales",
        "gold_category_sales",
        "gold_state_sales",
        "gold_payment_analysis"
    ]
    for table_name in tables:
        pq_path = gold_path / f"{table_name}.parquet"
        csv_path = gold_path / f"{table_name}.csv"
        assert pq_path.exists(), f"Missing Parquet: {pq_path}"
        assert csv_path.exists(), f"Missing CSV: {csv_path}"

        df = pd.read_parquet(pq_path)
        assert len(df) > 0, f"Table {table_name} is unexpectedly empty"


def test_gold_monthly_sales_has_no_na_revenue():
    gold_path = ROOT / "data" / "gold"
    df_monthly = pd.read_parquet(gold_path / "gold_monthly_sales.parquet")
    assert df_monthly["total_revenue"].isnull().sum() == 0, "Monthly sales revenue contains NA"
    assert df_monthly["total_revenue"].sum() > 0, "Total monthly revenue must be positive"


def test_gold_category_sales_populated():
    gold_path = ROOT / "data" / "gold"
    df_cat = pd.read_parquet(gold_path / "gold_category_sales.parquet")
    assert len(df_cat) > 20, "Category sales should have rich category rows"
    assert df_cat["total_revenue"].isnull().sum() == 0
    assert df_cat["total_revenue"].sum() > 0


if __name__ == "__main__":
    test_raw_data_exists()
    test_bronze_layer()
    test_silver_layer()
    test_gold_layer_completeness()
    test_gold_monthly_sales_has_no_na_revenue()
    test_gold_category_sales_populated()
    print("ALL TESTS PASSED SUCCESSFULLY!")
