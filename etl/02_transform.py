"""
ETL Script 02 — Transform
Raw CSVs clean karo aur data/clean/ mein save karo
"""

import pandas as pd
import re
import os

RAW_DIR   = "data/raw"
CLEAN_DIR = "data/clean"

os.makedirs(CLEAN_DIR, exist_ok=True)

# ── Helpers ──────────────────────────────────────────────

def parse_pct(val):
    """'10 Years: 21%' → 21.0"""
    if pd.isna(val):
        return None
    match = re.search(r"[\d.]+%", str(val))
    return float(match.group().replace("%", "")) if match else None

def parse_label(val):
    """'10 Years: 21%' → '10 Years'"""
    if pd.isna(val):
        return None
    match = re.match(r"(\d+\s*Years?|TTM)", str(val).strip(), re.IGNORECASE)
    return match.group().strip() if match else None

# ── 1. Companies ─────────────────────────────────────────

def transform_companies():
    df = pd.read_csv(f"{RAW_DIR}/companies_raw.csv")
    df = df[["symbol", "company_name", "sector", "face_value",
             "book_value", "roce_percentage", "roe_percentage"]]
    df = df.dropna(subset=["symbol", "company_name"])
    df.to_csv(f"{CLEAN_DIR}/companies.csv", index=False)
    print(f"companies     → {len(df)} rows")

# ── 2. Dim tables ─────────────────────────────────────────

def transform_dims():
    companies = pd.read_csv(f"{CLEAN_DIR}/companies.csv")

    # dim_sector
    sectors = companies[["sector"]].drop_duplicates().dropna()
    sectors.columns = ["sector_name"]
    sectors.to_csv(f"{CLEAN_DIR}/sectors.csv", index=False)

    # dim_year — 2012 to 2024
    years = pd.DataFrame({
        "year_id":    range(2012, 2025),
        "year_label": [f"FY{y}" for y in range(2012, 2025)]
    })
    years.to_csv(f"{CLEAN_DIR}/years.csv", index=False)

    # dim_health_label
    labels = pd.DataFrame({"label_name": ["EXCELLENT", "GOOD", "AVERAGE", "WEAK", "POOR"]})
    labels.to_csv(f"{CLEAN_DIR}/healthlabels.csv", index=False)

    print(f"dim_sector    → {len(sectors)} rows")
    print(f"dim_year      → {len(years)} rows")
    print(f"dim_health    → 5 rows")

# ── 3. Profit & Loss ──────────────────────────────────────

def transform_profit_loss():
    df = pd.read_csv(f"{RAW_DIR}/profitloss_raw.csv")
    df = df.rename(columns={"opm_percentage": "opm_pct"})
    df["year"] = df["year"].astype(str).str.strip()
    df = df.dropna(subset=["symbol", "year", "sales"])
    df.to_csv(f"{CLEAN_DIR}/profitandloss.csv", index=False)
    print(f"profit_loss   → {len(df)} rows")

# ── 4. Balance Sheet ──────────────────────────────────────

def transform_balance_sheet():
    df = pd.read_csv(f"{RAW_DIR}/balancesheet_raw.csv")
    df["year"] = df["year"].astype(str).str.strip()
    df["debt_to_equity"] = (
        df["borrowings"] / (df["equity_capital"] + df["reserves"])
    ).round(2)
    df = df.dropna(subset=["symbol", "year"])
    df.to_csv(f"{CLEAN_DIR}/balancesheet.csv", index=False)
    print(f"balance_sheet → {len(df)} rows")

# ── 5. Cash Flow ──────────────────────────────────────────

def transform_cash_flow():
    df = pd.read_csv(f"{RAW_DIR}/cashflow_raw.csv")
    df["year"] = df["year"].astype(str).str.strip()
    df["free_cash_flow"] = df["operating_activity"] + df["investing_activity"]
    df = df.dropna(subset=["symbol", "year"])
    df.to_csv(f"{CLEAN_DIR}/cashflow.csv", index=False)
    print(f"cash_flow     → {len(df)} rows")

# ── 6. Analysis ───────────────────────────────────────────

def transform_analysis():
    df = pd.read_csv(f"{RAW_DIR}/analysis_raw.csv")

    # Parse CAGR strings → numbers
    df["period"]          = df["compounded_sales_growth"].apply(parse_label)
    df["sales_cagr"]      = df["compounded_sales_growth"].apply(parse_pct)
    df["profit_cagr"]     = df["compounded_profit_growth"].apply(parse_pct)
    df["stock_cagr"]      = df["stock_price_cagr"].apply(parse_pct)
    df["roe_pct"]         = df["roe"].apply(parse_pct)

    df = df[["symbol", "period", "sales_cagr", "profit_cagr", "stock_cagr", "roe_pct"]]
    df = df.dropna(subset=["symbol"])
    df.to_csv(f"{CLEAN_DIR}/analysis.csv", index=False)
    print(f"analysis      → {len(df)} rows")

# ── 7. Pros & Cons ────────────────────────────────────────

def transform_pros_cons():
    df = pd.read_csv(f"{RAW_DIR}/proscons_raw.csv")

    rows = []
    for _, row in df.iterrows():
        if pd.notna(row["pros"]):
            rows.append({
                "symbol":   row["symbol"],
                "is_pro":   True,
                "category": "General",
                "text":     str(row["pros"]).strip()
            })
        if pd.notna(row["cons"]):
            rows.append({
                "symbol":   row["symbol"],
                "is_pro":   False,
                "category": "General",
                "text":     str(row["cons"]).strip()
            })

    result = pd.DataFrame(rows)
    result.to_csv(f"{CLEAN_DIR}/prosandcons.csv", index=False)
    print(f"pros_cons     → {len(result)} rows")

# ── Run ───────────────────────────────────────────────────

if __name__ == "__main__":
    print("=== Transform Start ===")
    transform_companies()
    transform_dims()
    transform_profit_loss()
    transform_balance_sheet()
    transform_cash_flow()
    transform_analysis()
    transform_pros_cons()
    print("=== Transform Done ===")