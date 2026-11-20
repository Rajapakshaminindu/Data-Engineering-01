# RetailFlow – Power BI Dashboard Guide

This guide details how to load the Gold analytical layer into **Microsoft Power BI Desktop**, configure the data model, create DAX measures, and replicate the executive business intelligence dashboards.

---

## 1. Data Sources

The clean, business-ready Gold layer is exported in both `.csv` and `.parquet` in:
- `RetailFlow/powerbi/data/*.csv`
- `RetailFlow/data/gold/*.parquet`

### Files to Import:
1. `gold_order_summary.csv` (Order-level central fact table)
2. `gold_monthly_sales.csv` (Monthly sales and revenue trend dimension)
3. `gold_category_sales.csv` (Product category performance dimension)
4. `gold_state_sales.csv` (Geographic distribution dimension)
5. `gold_payment_analysis.csv` (Payment method transaction dimension)

---

## 2. Data Modeling & Star Schema

In Power BI **Model View**, set up relationships:

```
          [gold_monthly_sales]
                   │
                   │ (sales_month)
                   ▼
[gold_category_sales] ────► [gold_order_summary] ◄──── [gold_state_sales]
(category)                          │                   (customer_state)
                                    │
                                    ▼
                         [gold_payment_analysis]
                             (payment_type)
```

- **Fact Table:** `gold_order_summary`
- **Dimension Tables:** `gold_monthly_sales`, `gold_category_sales`, `gold_state_sales`, `gold_payment_analysis`
- **Cardinality:** 1-to-many (`1:*`) with single cross-filter direction.

---

## 3. Key DAX Measures

All measures are provided in [`dax_measures.dax`](./dax_measures.dax).

| Measure | DAX Formula | Purpose |
|---|---|---|
| **Total Revenue** | `SUM(gold_order_summary[payment_total])` | Overall business gross revenue |
| **Total Orders** | `DISTINCTCOUNT(gold_order_summary[order_id])` | Total orders processed |
| **Average Order Value (AOV)** | `DIVIDE([Total Revenue], [Total Orders], 0)` | Average value per order |
| **Delivery Success Rate** | `DIVIDE([Total Delivered Orders], [Total Orders], 0)` | Fulfillment completion % |
| **Total Unique Customers** | `DISTINCTCOUNT(gold_order_summary[customer_unique_id])` | Unique purchasing customers |
| **Average Delivery Time** | `AVERAGE(gold_order_summary[delivery_days])` | Days taken from order to delivery |

---

## 4. Dashboard Pages & Visual Specifications

### Page 1: Executive Sales & Revenue Overview
- **Top KPI Cards:**
  - Total Revenue: `$15.8M`
  - Total Orders: `99,441`
  - Average Order Value (AOV): `$159.20`
  - Delivery Success Rate: `97.0%`
  - Total Customers: `96,096`
- **Monthly Revenue Trend:** Combo Line & Clustered Column Chart (`sales_month` on X-axis, `total_revenue` on Y-axis).
- **Top Product Categories:** Horizontal Clustered Bar Chart (`product_category_name_english` vs `total_revenue`).
- **Revenue by Payment Method:** Donut Chart (`payment_type` vs `total_payment_value`).
- **Revenue by State:** Clustered Bar Chart / Map (`customer_state` vs `total_revenue`).

### Page 2: Customer & Delivery Operations Performance
- **Top KPI Cards:**
  - Delivered Orders: `96,478`
  - Cancelled Orders: `625`
  - Delivery Lead Time: `12.5 Days`
  - On-Time Delivery Rate: `92.1%`
- **Order Status Distribution:** Donut Chart (`order_status` breakdown).
- **Delivery Lead Time by State:** Clustered Column Chart (`customer_state` vs `delivery_days`).
- **Monthly Order Fulfillment Trend:** Stacked Area Chart.
