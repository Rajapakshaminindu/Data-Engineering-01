# RetailFlow – End-to-End Data Engineering Lakehouse

**Building a modern data engineering pipeline using real-world e-commerce data.**

## About the Project

RetailFlow is an end-to-end data engineering project designed to demonstrate how raw business data can be collected, processed, cleaned, stored, and transformed into useful information for business analysis.

The project uses the **Olist Brazilian E-Commerce Public Dataset** to build a modern data pipeline based on the Medallion Architecture.

The main goal is to develop practical skills in data engineering, big data processing, cloud data platforms, and business intelligence.

## Project Goals

- Build a complete data ingestion and processing pipeline.
- Work with real-world datasets.
- Apply data cleaning and transformation techniques.
- Understand Medallion Architecture (Bronze, Silver, and Gold).
- Build a data warehouse using a Star Schema.
- Explore big data processing with Apache Spark.
- Integrate cloud data engineering services.
- Create business intelligence dashboards.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Data processing and automation |
| Pandas & NumPy | Data exploration and manipulation |
| SQL | Data querying and transformation |
| Apache Spark / PySpark | Large-scale data processing |
| Databricks | Data engineering and lakehouse development |
| Delta Lake | Reliable data storage |
| Microsoft Fabric | Cloud data engineering |
| Power BI | Data visualization and reporting |
| Git & GitHub | Version control and project management |

*Some technologies will be introduced in later development stages.*

## Data Source

**Dataset:** Olist Brazilian E-Commerce Public Dataset

Source: [Kaggle – Olist Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)

The dataset contains information about:
- Customer orders
- Customers and sellers
- Products
- Payments
- Reviews
- Order delivery information

## Planned Architecture

The project will follow the Medallion Architecture:

**Bronze Layer**
- Store raw data.
- Maintain the original source information.

**Silver Layer**
- Clean and validate data.
- Handle missing values and duplicates.
- Transform data into a consistent format.

**Gold Layer**
- Create business-ready datasets.
- Build fact and dimension tables.
- Prepare data for reporting and analysis.

## Project Structure

```text
RetailFlow/
│
├── data/
│   ├── raw/
│   └── sample/
│
├── notebooks/
├── ingestion/
├── sql/
├── tests/
├── docs/
├── powerbi/
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Development Roadmap

- [x] Project environment setup
- [x] Python libraries installation
- [x] Dataset preparation
- [x] Initial data exploration
- [ ] Data quality analysis
- [ ] Python data ingestion pipeline
- [ ] Bronze, Silver, and Gold layers
- [ ] Apache Spark and Delta Lake integration
- [ ] SQL data warehouse and Star Schema
- [ ] Microsoft Fabric integration
- [ ] Power BI dashboard
- [ ] Pipeline automation and testing

## Project Status

**Currently in development – Phase 1: Data Exploration.**

This project is being developed step by step as a practical data engineering learning journey.

## Author

**Minindu Rajapaksha**

Software Engineering Undergraduate  
Interested in Data Engineering, Data Science, and Cloud Technologies.

[GitHub](https://github.com/)
