-- ====================================================================
-- RetailFlow Data Warehouse - Key Analytical Business Queries
-- Used for Power BI Verification & Executive Reporting
-- ====================================================================

-- 1. Monthly Revenue & Orders Growth
SELECT 
    TO_CHAR(order_purchase_timestamp, 'YYYY-MM') AS sales_month,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    ROUND(SUM(product_revenue), 2) AS total_revenue,
    ROUND(SUM(shipping_cost), 2) AS total_shipping,
    ROUND(SUM(payment_total), 2) AS total_payment,
    ROUND(AVG(payment_total), 2) AS avg_order_value
FROM fact_orders
WHERE order_status = 'delivered'
GROUP BY 1
ORDER BY 1;

-- 2. Top 10 Product Categories by Revenue
SELECT 
    p.product_category_name_english,
    COUNT(f.order_id) AS total_orders,
    ROUND(SUM(f.product_revenue), 2) AS total_revenue,
    ROUND(AVG(f.product_revenue), 2) AS avg_revenue_per_order
FROM fact_orders f
JOIN dim_products p ON 1=1 -- Linked via order items in data lake
WHERE f.order_status = 'delivered'
GROUP BY p.product_category_name_english
ORDER BY total_revenue DESC
LIMIT 10;

-- 3. Top States by Sales and Delivery SLA
SELECT 
    customer_state,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(payment_total), 2) AS total_revenue,
    ROUND(AVG(delivery_days), 1) AS avg_delivery_days,
    ROUND((1.0 - (SUM(is_delayed)::FLOAT / COUNT(*))) * 100, 2) AS on_time_delivery_rate_pct
FROM fact_orders
WHERE order_status = 'delivered'
GROUP BY customer_state
ORDER BY total_revenue DESC;

-- 4. Payment Method Contribution
SELECT 
    primary_payment_type,
    COUNT(order_id) AS total_transactions,
    ROUND(SUM(payment_total), 2) AS total_payment,
    ROUND((SUM(payment_total) / (SELECT SUM(payment_total) FROM fact_orders WHERE order_status = 'delivered')) * 100, 2) AS revenue_share_pct
FROM fact_orders
WHERE order_status = 'delivered'
GROUP BY primary_payment_type
ORDER BY total_payment DESC;
