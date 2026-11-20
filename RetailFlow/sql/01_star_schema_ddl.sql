-- ====================================================================
-- RetailFlow Data Warehouse - Star Schema DDL
-- Lakehouse Dimensional Modeling
-- ====================================================================

-- 1. Dim Customers
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_id VARCHAR(64) PRIMARY KEY,
    customer_unique_id VARCHAR(64) NOT NULL,
    customer_zip_code_prefix VARCHAR(10),
    customer_city VARCHAR(100),
    customer_state CHAR(2)
);

-- 2. Dim Products
CREATE TABLE IF NOT EXISTS dim_products (
    product_id VARCHAR(64) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_category_name_english VARCHAR(100),
    product_name_length INT,
    product_description_length INT,
    product_photos_qty INT,
    product_weight_g FLOAT,
    product_length_cm FLOAT,
    product_height_cm FLOAT,
    product_width_cm FLOAT
);

-- 3. Dim Date (Derived from Sales Months)
CREATE TABLE IF NOT EXISTS dim_date (
    sales_month VARCHAR(7) PRIMARY KEY,
    year INT,
    month INT,
    quarter INT
);

-- 4. Dim Payment Types
CREATE TABLE IF NOT EXISTS dim_payments (
    payment_type VARCHAR(32) PRIMARY KEY,
    description VARCHAR(100)
);

-- 5. Fact Orders (Central Business Fact Table)
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) REFERENCES dim_customers(customer_id),
    order_status VARCHAR(20),
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,
    total_items INT DEFAULT 1,
    product_revenue NUMERIC(12, 2) DEFAULT 0.00,
    shipping_cost NUMERIC(12, 2) DEFAULT 0.00,
    payment_total NUMERIC(12, 2) DEFAULT 0.00,
    primary_payment_type VARCHAR(32) REFERENCES dim_payments(payment_type),
    customer_state CHAR(2),
    delivery_days FLOAT,
    is_delayed SMALLINT DEFAULT 0
);
