"""
ETL step 1 — load the raw Ergast F1 CSVs into a SQLite database.

Reads every CSV in data/raw/, cleans Ergast's '\N' null markers, and writes
each file as a table in data/f1.db. Re-running it rebuilds the database from
scratch, so it is safe to run as often as you like.

Run it with the project's virtual environment:
    .\.venv\Scripts\python.exe etl\load_data.py
"""

# what the load_data.py and query.py scripts do, and how to run them?

# A Python ETL script reads the CSVs with pandas, cleans the missing-value markers, 
# and loads each into a SQLite table; a second script runs SQL queries against it.

import sqlite3 # talk to a SQLite database (built into Python)
from pathlib import Path # handle file paths cleanly
import pandas as pd

# Resolve paths relative to THIS file, so the script works no matter what
# folder you run it from.
ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
DB_PATH = ROOT / "data" / "f1.db"


def load() -> None:
    csv_files = sorted(RAW_DIR.glob("*.csv"))   # find all 14 CSV files
    if not csv_files:
        raise SystemExit(f"No CSV files found in {RAW_DIR}. Did the download land there?")

    print(f"Building database: {DB_PATH}\n")
    conn = sqlite3.connect(DB_PATH) # open (or create) the database 
    try:
        for csv_path in csv_files:
            table_name = csv_path.stem  # e.g. "lap_times.csv" -> table "lap_times"
            # .stem -> filenmaes without the extension becomes the table name

            # Ergast uses the text '\N' to mean "missing value" — tell pandas to
            # read those as proper NULLs instead of the literal string.
            df = pd.read_csv(csv_path, na_values=[r"\N"])

            # Write the DataFrame to a table. if_exists="replace" makes this
            # re-runnable: it drops and recreates the table each time.
            df.to_sql(table_name, conn, if_exists="replace", index=False)

            print(f"  {table_name:<24} {len(df):>7,} rows  x {len(df.columns)} cols")
    finally:
        conn.close()

    print("\nDone. data/f1.db is ready to query.")


if __name__ == "__main__":
    load()

