"""
Script 02 — ETL: Load Cleaned CSV -> SQLite Database
====================================================
This script is structured so it can be run:
  - Manually:               python scripts/02_etl_to_sqlite.py
  - On a schedule (Windows): Task Scheduler → Action: python <path>\\02_etl_to_sqlite.py
  - On a schedule (Linux/Mac): cron → 0 6 * * 1 python /path/to/02_etl_to_sqlite.py

The core logic lives in run() so it can also be imported and called
from an orchestrator (e.g., Airflow, Prefect, or a simple wrapper).

What this script does:
  1. Reads the cleaned CSV produced by 01_clean_data.py
  2. Connects to (or creates) database/sales.db
  3. Drops and recreates the `sales` table on each run
     → This is a "full refresh" pattern — safe for a ~10 K row dataset.
       For incremental loads on large data, you'd switch to UPSERT logic.
  4. Writes all rows to SQLite
  5. Runs a quick row-count verification to confirm the load succeeded
"""

import os
import sqlite3
import pandas as pd

# ─── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_PATH = os.path.join(BASE_DIR, "data", "cleaned", "superstore_cleaned.csv")
DB_PATH    = os.path.join(BASE_DIR, "database", "sales.db")

# Table name in SQLite
TABLE_NAME = "sales"


# ─── Step 1: Load cleaned CSV ─────────────────────────────────────────────────
def load_cleaned_csv(path: str) -> pd.DataFrame:
    """Read the cleaned CSV; date columns are stored as strings in SQLite."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Cleaned CSV not found: {path}\n"
            "Please run  python scripts/01_clean_data.py  first."
        )
    df = pd.read_csv(path, low_memory=False)
    print(f"[LOAD] Read {len(df):,} rows from {path}")
    return df


# ─── Step 2: Write to SQLite ──────────────────────────────────────────────────
def write_to_sqlite(df: pd.DataFrame, db_path: str, table: str) -> None:
    """
    Full-refresh load:
      - DROP the table if it exists
      - CREATE it fresh with inferred column types
      - INSERT all rows via pandas .to_sql()

    For a production pipeline you would:
      - Add a 'loaded_at' audit column
      - Use INSERT OR REPLACE (UPSERT) on a primary key
      - Log load metadata to a separate audit table
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    try:
        df.to_sql(table, conn, if_exists="replace", index=False)
        print(f"[ETL] Wrote {len(df):,} rows -> {db_path}  (table: {table})")
    finally:
        conn.close()


# ─── Step 3: Verify ───────────────────────────────────────────────────────────
def verify_load(db_path: str, table: str, expected_rows: int) -> None:
    """
    Confirm the row count in SQLite matches the source CSV.
    Raises if there's a mismatch — useful when running on a schedule.
    """
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(f"SELECT COUNT(*) FROM {table};")
        db_rows = cursor.fetchone()[0]
    finally:
        conn.close()

    if db_rows != expected_rows:
        raise RuntimeError(
            f"[ERROR] Row count mismatch! "
            f"CSV: {expected_rows:,}  |  SQLite: {db_rows:,}"
        )
    print(f"[VERIFY] Row count matches: {db_rows:,} rows in SQLite [OK]")


# ─── Step 4: Show column info ─────────────────────────────────────────────────
def print_schema(db_path: str, table: str) -> None:
    """Print the SQLite table schema — useful for debugging and documentation."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.execute(f"PRAGMA table_info({table});")
        cols = cursor.fetchall()
        print(f"\n[SCHEMA] Table '{table}' — {len(cols)} columns:")
        print(f"  {'cid':<4} {'name':<30} {'type':<15} {'notnull':<10} {'pk'}")
        print(f"  {'-'*4} {'-'*30} {'-'*15} {'-'*10} {'-'*5}")
        for col in cols:
            print(f"  {col[0]:<4} {col[1]:<30} {col[2]:<15} {str(col[3]):<10} {col[5]}")
    finally:
        conn.close()


# ─── Orchestrator entry point ─────────────────────────────────────────────────
def run():
    """
    Main ETL function.
    Separated from __main__ so this can be imported and called
    by a scheduler or orchestration tool.
    """
    print("=" * 60)
    print("  Sales Analytics Pipeline — Step 2: ETL to SQLite")
    print("=" * 60)

    df = load_cleaned_csv(CLEAN_PATH)
    write_to_sqlite(df, DB_PATH, TABLE_NAME)
    verify_load(DB_PATH, TABLE_NAME, expected_rows=len(df))
    print_schema(DB_PATH, TABLE_NAME)

    print("\n[DONE] ETL complete. Database ready at:")
    print(f"       {DB_PATH}")
    print("\nTo query the database:")
    print("  Option A (Python): import sqlite3; conn = sqlite3.connect('database/sales.db')")
    print("  Option B (CLI):    sqlite3 database/sales.db")
    print("  Option C (GUI):    DB Browser for SQLite — https://sqlitebrowser.org\n")


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run()
