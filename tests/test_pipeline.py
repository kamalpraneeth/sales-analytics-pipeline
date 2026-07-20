"""
tests/test_pipeline.py — Automated Pipeline Verification
=========================================================
Runs 4 checks against the outputs of the two scripts:
  Check 1: Cleaned CSV — no nulls in critical columns
  Check 2: Cleaned CSV — profit_margin values are within a sane range
  Check 3: SQLite DB   — row count matches cleaned CSV (ETL completeness)
  Check 4: SQLite DB   — all 6 expected derived columns are present

How to run:
  python tests/test_pipeline.py

  OR with pytest (if installed):
  pytest tests/test_pipeline.py -v

Prerequisites:
  Run 01_clean_data.py and 02_etl_to_sqlite.py before running tests.
"""

import os
import sys
import sqlite3
import pandas as pd

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_PATH = os.path.join(BASE_DIR, "data", "cleaned", "superstore_cleaned.csv")
DB_PATH    = os.path.join(BASE_DIR, "database", "sales.db")
TABLE      = "sales"


# ─── Helper ───────────────────────────────────────────────────────────────────
def pass_fail(name: str, condition: bool, detail: str = "") -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}")
    if detail:
        print(f"           {detail}")
    return condition


# ─── Check 1: No nulls in critical columns ────────────────────────────────────
def check_no_nulls_in_critical_columns() -> bool:
    """
    After cleaning, these columns must have zero nulls.
    A null here would break every downstream SQL query.
    """
    critical_cols = ["order_id", "sales", "profit", "quantity",
                     "category", "region", "segment"]

    df = pd.read_csv(CLEAN_PATH, low_memory=False)
    present_cols = [c for c in critical_cols if c in df.columns]
    null_counts  = df[present_cols].isnull().sum()
    has_nulls    = null_counts[null_counts > 0]

    ok = has_nulls.empty
    detail = "No nulls found [OK]" if ok else f"Nulls found:\n{has_nulls.to_string()}"
    return pass_fail("No nulls in critical columns", ok, detail)


# ─── Check 2: Profit margin values are sane ───────────────────────────────────
def check_profit_margin_range() -> bool:
    """
    profit_margin = profit / sales.
    Expected range: -1.0 to +1.0 (i.e., -100% to +100%).
    Values outside this suggest a data quality problem (e.g., price/cost error).
    We allow a tiny tolerance for floating-point edge cases.
    """
    df = pd.read_csv(CLEAN_PATH, low_memory=False)
    margin = df["profit_margin"].dropna()

    lower, upper = -1.05, 1.05     # 5% tolerance beyond ±100%
    out_of_range  = margin[(margin < lower) | (margin > upper)]
    ok = len(out_of_range) == 0

    detail = (
        f"Min={margin.min():.4f}  Max={margin.max():.4f}  "
        f"Mean={margin.mean():.4f}  (all within [{lower}, {upper}]) [OK]"
        if ok else
        f"{len(out_of_range)} values outside [{lower}, {upper}]: "
        f"Min={margin.min():.4f}  Max={margin.max():.4f}"
    )
    return pass_fail("Profit margin values within sane range [-1.05, +1.05]", ok, detail)


# ─── Check 3: Row count matches between CSV and SQLite ───────────────────────
def check_row_count_matches() -> bool:
    """
    The SQLite table must contain exactly the same number of rows as the
    cleaned CSV.  A mismatch means the ETL dropped or duplicated records.
    """
    df = pd.read_csv(CLEAN_PATH, low_memory=False)
    csv_rows = len(df)

    conn = sqlite3.connect(DB_PATH)
    try:
        db_rows = conn.execute(f"SELECT COUNT(*) FROM {TABLE};").fetchone()[0]
    finally:
        conn.close()

    ok = csv_rows == db_rows
    detail = (
        f"CSV rows: {csv_rows:,}  |  SQLite rows: {db_rows:,} [OK]"
        if ok else
        f"CSV rows: {csv_rows:,}  |  SQLite rows: {db_rows:,}  ← MISMATCH"
    )
    return pass_fail("Row count: cleaned CSV == SQLite table", ok, detail)


# ─── Check 4: All derived columns are present ─────────────────────────────────
def check_derived_columns_exist() -> bool:
    """
    Verify that all 6 derived columns created in 01_clean_data.py are
    present in the cleaned CSV (and therefore in the SQLite table).
    Missing columns means feature engineering was skipped or renamed.
    """
    expected = [
        "profit_margin",
        "order_to_ship_days",
        "order_year",
        "order_month",
        "order_quarter",
        "order_month_name",
    ]
    df = pd.read_csv(CLEAN_PATH, nrows=1, low_memory=False)   # read 1 row = fast
    missing = [c for c in expected if c not in df.columns]
    ok = len(missing) == 0
    detail = (
        f"All {len(expected)} derived columns present [OK]"
        if ok else
        f"Missing columns: {missing}"
    )
    return pass_fail("All 6 derived columns exist in cleaned CSV", ok, detail)


# ─── Runner ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Sales Analytics Pipeline — Test Suite")
    print("=" * 60)

    # Pre-flight: check files exist before running checks
    errors = []
    if not os.path.exists(CLEAN_PATH):
        errors.append(f"Missing: {CLEAN_PATH}  →  run 01_clean_data.py first")
    if not os.path.exists(DB_PATH):
        errors.append(f"Missing: {DB_PATH}  →  run 02_etl_to_sqlite.py first")

    if errors:
        print("\n[ERROR] Cannot run tests — prerequisites missing:")
        for e in errors:
            print(f"  • {e}")
        sys.exit(1)

    print()
    results = [
        check_no_nulls_in_critical_columns(),
        check_profit_margin_range(),
        check_row_count_matches(),
        check_derived_columns_exist(),
    ]

    passed = sum(results)
    total  = len(results)
    print(f"\n{'-' * 40}")
    print(f"  Result: {passed}/{total} checks passed")
    print("-" * 40)

    if passed == total:
        print("  All checks passed — pipeline output is valid [OK]\n")
    else:
        print("  Some checks failed — review output above [FAIL]\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
