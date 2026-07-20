"""
Script 01 — Download & Clean the Superstore Sales Dataset
==========================================================
Dataset Source (exact, locked):
  Plotly public datasets mirror (no login required):
  https://raw.githubusercontent.com/plotly/datasets/master/superstore.csv

  Original dataset credit:
  "Sample - Superstore" by Tableau / Kaggle user vivek468
  https://www.kaggle.com/datasets/vivek468/superstore-dataset-final

What this script does:
  1. Downloads the raw CSV from the locked URL (skip if already present)
  2. Cleans: standardise column names, parse dates, remove duplicates,
     handle missing values, fix numeric dtypes
  3. Engineers derived columns for analysis:
       - profit_margin        (profit / sales)
       - order_to_ship_days  (Ship Date - Order Date)
       - order_year, order_month, order_quarter
       - revenue_per_unit     (sales / quantity)
  4. Saves cleaned data → data/cleaned/superstore_cleaned.csv

Run:
  python scripts/01_clean_data.py
"""

import os
import requests
import pandas as pd

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH   = os.path.join(BASE_DIR, "data", "raw",     "superstore_raw.csv")
CLEAN_PATH = os.path.join(BASE_DIR, "data", "cleaned", "superstore_cleaned.csv")

# Exact dataset URL — do not change
RAW_URL = "https://raw.githubusercontent.com/plotly/datasets/master/superstore.csv"


# ─── Step 1: Download ─────────────────────────────────────────────────────────
def download_raw(url: str, dest: str) -> None:
    """Download raw CSV from the locked URL if not already present locally."""
    if os.path.exists(dest):
        print(f"[SKIP] Raw file already exists: {dest}")
        return

    print(f"[DOWNLOAD] Fetching: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(response.content)
        print(f"[OK] Saved raw data -> {dest}")
    except Exception as e:
        raise RuntimeError(
            f"Failed to download dataset: {e}\n"
            "Please check your internet connection or download manually from:\n"
            f"  {url}\n"
            f"and place it at: {dest}"
        )


# ─── Step 2: Load ─────────────────────────────────────────────────────────────
def load_raw(path: str) -> pd.DataFrame:
    """Load the raw CSV, trying common encodings gracefully."""
    for encoding in ["utf-8", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(path, encoding=encoding)
            print(f"[LOAD] {len(df):,} rows × {len(df.columns)} columns  (encoding={encoding})")
            return df
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Cannot read {path} with any known encoding.")


# ─── Step 3: Clean ────────────────────────────────────────────────────────────
def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleaning rules applied (in order):
      a) Standardise column names → snake_case
      b) Parse date columns (Order Date, Ship Date)
      c) Remove exact duplicate rows
      d) Report and drop rows with nulls in critical columns
      e) Fill postal_code nulls (label field, not numeric)
      f) Coerce numeric columns to float
    """
    # a) Column names -> snake_case
    df.columns = (
        df.columns
          .str.strip()
          .str.lower()
          .str.replace(r"[\s\-/]+", "_", regex=True)
          .str.replace(r"[^a-z0-9_]", "", regex=True)
    )
    print(f"[CLEAN] Columns after rename: {list(df.columns)}")

    # b) Parse dates
    for col in ["order_date", "ship_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            nat_count = df[col].isna().sum()
            if nat_count:
                print(f"  [WARN] {nat_count} unparseable dates in '{col}' -> NaT")

    # c) Remove duplicates
    before = len(df)
    df = df.drop_duplicates()
    removed = before - len(df)
    print(f"[CLEAN] Duplicates removed: {removed:,}  (rows remaining: {len(df):,})")

    # d) Missing value audit
    missing = df.isnull().sum()
    missing_cols = missing[missing > 0]
    if not missing_cols.empty:
        print("[CLEAN] Missing values per column:")
        print(missing_cols.to_string())
    else:
        print("[CLEAN] No missing values found [OK]")

    # Drop rows missing any critical business column
    critical = [c for c in ["order_id", "sales", "profit", "quantity"] if c in df.columns]
    before = len(df)
    df = df.dropna(subset=critical)
    dropped = before - len(df)
    if dropped:
        print(f"[CLEAN] Dropped {dropped:,} rows missing: {critical}")

    # e) postal_code is a label — fill nulls with '00000'
    if "postal_code" in df.columns:
        df["postal_code"] = df["postal_code"].fillna(0).astype(int).astype(str)

    # f) Ensure numeric dtypes
    for col in ["sales", "profit", "quantity", "discount"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# ─── Step 4: Feature Engineering ─────────────────────────────────────────────
def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derived columns created here are the ones used directly in SQL analysis
    and Power BI visuals.

    Column              | Formula                          | Used for
    ─────────────────────────────────────────────────────────────────────
    profit_margin       | profit / sales                   | KPI card, ranking
    order_to_ship_days  | ship_date - order_date (days)   | Operations analysis
    order_year          | order_date.year                  | Time filtering
    order_month         | order_date.month (1-12)          | Trend chart
    order_quarter       | order_date.quarter (1-4)         | Quarterly rollup
    order_month_name    | "Jan 2021" format                | Axis labels in PBI
    revenue_per_unit    | sales / quantity                 | Product comparison
    """

    # Profit margin (guard against division by zero)
    df["profit_margin"] = (
        df["profit"] / df["sales"].replace(0, pd.NA)
    ).round(4)

    # Fulfilment lead time
    if "order_date" in df.columns and "ship_date" in df.columns:
        df["order_to_ship_days"] = (df["ship_date"] - df["order_date"]).dt.days

    # Time dimensions
    if "order_date" in df.columns:
        df["order_year"]       = df["order_date"].dt.year
        df["order_month"]      = df["order_date"].dt.month
        df["order_quarter"]    = df["order_date"].dt.quarter
        df["order_month_name"] = df["order_date"].dt.strftime("%b %Y")

    # Revenue per unit sold
    if "quantity" in df.columns:
        df["revenue_per_unit"] = (
            df["sales"] / df["quantity"].replace(0, pd.NA)
        ).round(2)

    return df


# ─── Step 5: Save ─────────────────────────────────────────────────────────────
def save_clean(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[SAVE] Cleaned CSV -> {path}  ({len(df):,} rows × {len(df.columns)} cols)")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Sales Analytics Pipeline — Step 1: Download & Clean")
    print("=" * 60)

    download_raw(RAW_URL, RAW_PATH)
    df = load_raw(RAW_PATH)
    df = clean(df)
    df = add_derived_columns(df)
    save_clean(df, CLEAN_PATH)

    # Print a quick analyst summary
    print("\n--- Quick Stats -----------------------------------------")
    print(df[["sales", "profit", "profit_margin",
               "order_to_ship_days", "discount"]].describe().round(3).to_string())
    print("\n--- Sample Rows -----------------------------------------")
    cols = ["order_id", "category", "sales", "profit",
            "profit_margin", "order_to_ship_days", "order_year", "order_quarter"]
    print(df[[c for c in cols if c in df.columns]].head(5).to_string(index=False))
    print("\n[DONE] Step 1 complete.\n")


if __name__ == "__main__":
    main()
