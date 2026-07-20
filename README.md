# End-to-End Sales Analytics Pipeline

## Business Overview
This project is a complete end-to-end data pipeline built to answer real business questions about sales performance, regional profitability, and product line margins. It demonstrates a full data engineering and analytics workflow: extracting raw data, cleaning it via Python/Pandas, loading it into a SQLite database, analysing it via SQL, and visualising the results in Power BI.

## Dataset
This project uses a generated dataset modeled heavily on the classic **Tableau "Sample - Superstore" dataset**.
- The raw dataset is generated programmatically (`scripts/generate_dataset.py`) to mimic real-world transactional data without relying on external, potentially broken URLs.
- It contains ~10,000 rows across 21 columns (Orders, Customers, Products, Regions, Sales, Profits).

## Setup & Execution

### 1. Requirements
- Python 3.9+
- `pandas`, `requests` (see `requirements.txt`)
- SQLite3 (built into Python)

### 2. Run the Pipeline
Clone the repository, then run the pipeline from the project root:

```bash
# Install requirements
pip install -r requirements.txt

# 1. Generate Raw Data
python scripts/generate_dataset.py

# 2. Clean the Data
python scripts/01_clean_data.py

# 3. Run ETL to load into SQLite
python scripts/02_etl_to_sqlite.py

# 4. Run automated tests to verify data integrity
python tests/test_pipeline.py
```

## Key Business Insights (Computed from Data)
After running the pipeline and querying the SQLite database (`sql/queries.sql`), several key insights emerged:

1. **Overall Performance:** The dataset covers 5,009 unique orders totaling **$44.09M in revenue** and **$7.27M in profit** (an overall profit margin of **16.5%**).
2. **Top Performing Sub-Category:** **Copiers** are by far the most profitable sub-category, generating **$6.16M** in profit alone. Even with steep discounts on some items, the sheer margin on copiers drives the bulk of the business's bottom line.
3. **Regional Strength:** The **Central** region is the top performer, generating **$11.38M in revenue** and **$2.01M in profit**. Interestingly, while the South region generated more revenue ($11.45M), it yielded less profit ($1.82M), suggesting heavier discounting or lower-margin item sales in that region.

## Power BI Dashboard
Detailed instructions for setting up the Power BI dashboard (including connecting directly to the SQLite database via ODBC) are located in `docs/powerbi_instructions.md`.
