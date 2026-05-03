"""
ETL Script 03 — Load to PostgreSQL
Clean CSVs ko bluestock_dw database mein load karo
"""

import pandas as pd
from sqlalchemy import create_engine, text
import os

DB_USER     = "postgres"
DB_PASSWORD = "Ronit%40030473"
DB_HOST     = "localhost"
DB_PORT     = "5432"
DB_NAME     = "bluestock_dw"

CLEAN_DIR = "data/clean"

ENGINE_URL = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_engine():
    return create_engine(ENGINE_URL)


def load_table(engine, csv_file, table_name):
    path = os.path.join(CLEAN_DIR, csv_file)
    if not os.path.exists(path):
        print(f"   SKIP — file not found: {path}")
        return
    df = pd.read_csv(path)
    df.to_sql(table_name, con=engine, if_exists="replace",
              index=False, method="multi", chunksize=500)
    print(f"   {table_name:<25} {len(df)} rows loaded")


def apply_db_fixes(engine):
    print("\n Applying DB fixes...")
    with engine.connect() as conn:

        # fact_analysis mein CAGR columns add karo
        conn.execute(text("""
            ALTER TABLE fact_analysis
            ADD COLUMN IF NOT EXISTS sales_cagr_10y FLOAT,
            ADD COLUMN IF NOT EXISTS sales_cagr_5y  FLOAT,
            ADD COLUMN IF NOT EXISTS sales_cagr_3y  FLOAT,
            ADD COLUMN IF NOT EXISTS sales_cagr_ttm FLOAT,
            ADD COLUMN IF NOT EXISTS stock_cagr_10y FLOAT,
            ADD COLUMN IF NOT EXISTS stock_cagr_5y  FLOAT,
            ADD COLUMN IF NOT EXISTS stock_cagr_3y  FLOAT;
        """))

        conn.commit()
    print("   DB fixes applied!")


def run_load():
    print("=" * 50)
    print("ETL Step 03 — Load to bluestock_dw")
    print("=" * 50)

    print("\nConnecting to database...")
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Connected!\n")

    tables = [
        ("companies.csv",    "dim_company"),
        ("sectors.csv",      "dim_sector"),
        ("years.csv",        "dim_year"),
        ("healthlabels.csv", "dim_health_label"),
        ("profitandloss.csv","fact_profit_loss"),
        ("balancesheet.csv", "fact_balance_sheet"),
        ("cashflow.csv",     "fact_cash_flow"),
        ("analysis.csv",     "fact_analysis"),
        ("prosandcons.csv",  "fact_pros_cons"),
    ]

    print("Loading tables...")
    for csv_file, table_name in tables:
        load_table(engine, csv_file, table_name)

    apply_db_fixes(engine)

    print(f"\n{'='*50}")
    print("VERIFICATION — Row counts:")
    print(f"{'='*50}")
    with engine.connect() as conn:
        for _, table_name in tables:
            try:
                count = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table_name}")
                ).scalar()
                print(f"   {table_name:<25} {count} rows")
            except Exception as e:
                print(f"   {table_name:<25} ERROR: {e}")

    print("\n All done!")
    engine.dispose()


if __name__ == "__main__":
    run_load()