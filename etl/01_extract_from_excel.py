"""
ETL Script 01 — Extract from Excel
"""

import os
import pandas as pd

EXCEL_DIR = "data/excel_source"
OUTPUT_DIR = "data/raw"

FILES = {
    "companies.xlsx":     "companies.csv",
    "balancesheet.xlsx":  "balancesheet.csv",
    "cashflow.xlsx":      "cashflow.csv",
    "profitandloss.xlsx": "profitandloss.csv",
    "analysis.xlsx":      "analysis.csv",
    "documents.xlsx":     "documents.csv",
    "prosandcons.xlsx":   "prosandcons.csv",
}

HEADER_ROW = 1


def extract_table(excel_path, csv_path, table_name):
    print(f"\n{'='*50}")
    print(f"Reading: {table_name}")

    df = pd.read_excel(excel_path, header=HEADER_ROW)

    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    df.replace("nan", pd.NA, inplace=True)
    df.to_csv(csv_path, index=False, encoding="utf-8")

    print(f"  Rows   : {len(df)}")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Saved  : {csv_path}")

    return df


def run_extraction():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print("=" * 50)
    print("ETL Step 01 — Extract from Excel")
    print("=" * 50)

    all_dfs = {}

    for excel_file, csv_file in FILES.items():
        excel_path = os.path.join(EXCEL_DIR, excel_file)
        csv_path   = os.path.join(OUTPUT_DIR, csv_file)

        if not os.path.exists(excel_path):
            print(f"\n FILE NOT FOUND: {excel_path}")
            continue

        df = extract_table(excel_path, csv_path, excel_file)
        all_dfs[csv_file.replace(".csv", "")] = df

    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    for name, df in all_dfs.items():
        print(f"  {name:<20} {len(df)} rows")

    print(f"\nDone! CSVs saved in '{OUTPUT_DIR}/'")


if __name__ == "__main__":
    run_extraction()