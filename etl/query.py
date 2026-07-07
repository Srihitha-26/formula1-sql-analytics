r"""
Run a SQL query against data/f1.db and print the result as a table.

Usage (from the project root, using the venv's Python):
    .\.venv\Scripts\python.exe etl\query.py sql\00_example_top_wins.sql
    .\.venv\Scripts\python.exe etl\query.py "SELECT * FROM drivers LIMIT 5"

Give it either a path to a .sql file or a SQL string directly.
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "f1.db"


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Pass a .sql file path or a SQL string to run.")

    arg = sys.argv[1]
    candidate = Path(arg)
    if candidate.suffix.lower() == ".sql" and candidate.exists():
        sql = candidate.read_text(encoding="utf-8")
    else:
        sql = arg  # treat the argument itself as the query

    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(sql, conn)
    finally:
        conn.close()

    pd.set_option("display.max_rows", 100)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 50)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
