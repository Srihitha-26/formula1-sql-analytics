# Formula 1 SQL Analytics

An end-to-end data project analysing 70+ seasons of Formula 1 World Championship
data (1950–2024): raw CSVs → a normalised SQL database → analytical queries →
an interactive dashboard.

**Stack:** Python (ETL) · SQL (SQLite) · Streamlit dashboard *(planned)*

## What this project does
- Ingests the Ergast-schema F1 dataset (races, drivers, constructors, results,
  qualifying, lap times, pit stops, standings) from CSV.
- Loads it into a normalised SQLite database with a Python ETL script.
- Answers analytical questions in SQL using window functions, CTEs, and
  self-joins — championship progression, teammate head-to-head, grid-vs-finish
  trends, and pit-stop evolution.
- *(Planned)* Presents the findings in an interactive Streamlit dashboard.

## Project structure
```
data/raw/     # source CSVs (not committed — rebuilt by the ETL script)
etl/          # Python scripts that load the CSVs into the database
sql/          # schema definitions + analytical queries
dashboard/    # Streamlit app (later)
```

## Data source
Ergast-compatible Formula 1 dataset (CC BY-SA 4.0). Ergast's own API was retired
at the end of 2024; data is sourced from a maintained mirror of the same schema.

## Status
🚧 In progress — setting up the dataset and database schema.
