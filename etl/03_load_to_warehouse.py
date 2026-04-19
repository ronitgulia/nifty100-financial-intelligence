"""
ETL Script 03 — Load to PostgreSQL Warehouse
=============================================
Reads clean CSVs and loads them into nifty100 database.

Usage:
    python etl/03_load_to_warehouse.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text


DB_USER     = "postgres"
DB_PASSWORD = "Ronit%40030473"
DB_HOST     = "localhost"
DB_PORT     = "5432"
DB_NAME     = "nifty100"

CLEAN_DIR = "data/clean"

# Connection string
ENGINE_URL = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_engine():
    engine = create_engine(ENGINE_URL)
    return engine


def load_table(engine, csv_file, table_name):
    """CSV padhke PostgreSQL table mein load karo."""
    path = os.path.join(CLEAN_DIR, csv_file)

    if not os.path.exists(path):
        print(f"    File not found: {path}")
        return

    df = pd.read_csv(path)

    # Load karo — agar table pehle se hai toh replace karo
    df.to_sql(
        name=table_name,
        con=engine,
        if_exists="replace",   # pehli baar replace, baad mein upsert karenge
        index=False,
        method="multi",        # fast batch insert
        chunksize=500
    )

    print(f"   {table_name:<25} {len(df)} rows loaded")


def run_load():
    print("=" * 50)
    print("ETL Step 03 — Load to PostgreSQL")
    print("=" * 50)

    # Database connect karo
    print("\nConnecting to database...")
    engine = get_engine()

    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print(" Connected to nifty100 database!\n")

    # Tables load karo
    print("Loading tables...")
    tables = [
        ("companies.csv",     "dim_company"),
        ("balancesheet.csv",  "fact_balance_sheet"),
        ("cashflow.csv",      "fact_cash_flow"),
        ("profitandloss.csv", "fact_profit_loss"),
        ("analysis.csv",      "fact_analysis"),
        ("documents.csv",     "fact_documents"),
        ("prosandcons.csv",   "fact_pros_cons"),
    ]

    for csv_file, table_name in tables:
        load_table(engine, csv_file, table_name)

    # Verify — row counts check karo
    print(f"\n{'='*50}")
    print("VERIFICATION — Row counts in database:")
    print(f"{'='*50}")
    with engine.connect() as conn:
        for _, table_name in tables:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM {table_name}")
            )
            count = result.scalar()
            print(f"  {table_name:<25} {count} rows")

    print(f"\n All data loaded into PostgreSQL nifty100 database!")
    engine.dispose()


if __name__ == "__main__":
    run_load()