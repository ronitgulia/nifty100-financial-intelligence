"""
ETL Script 02 — Clean and Transform
=====================================
Reads CSVs from data/raw/, cleans them, adds computed columns,
and saves to data/clean/
"""

import os
import re
import pandas as pd
import numpy as np

RAW_DIR   = "data/raw"
CLEAN_DIR = "data/clean"

# ─────────────────────────────────────────────
# SECTOR MAPPING — 100 companies ka sector
# ─────────────────────────────────────────────
SECTOR_MAP = {
    # IT
    "TCS": "IT", "INFY": "IT", "WIPRO": "IT", "HCLTECH": "IT",
    "TECHM": "IT", "LTIM": "IT", "PERSISTENT": "IT", "COFORGE": "IT",
    # Banking
    "HDFCBANK": "Banking", "ICICIBANK": "Banking", "SBIN": "Banking",
    "AXISBANK": "Banking", "KOTAKBANK": "Banking", "BANKBARODA": "Banking",
    "CANBK": "Banking", "PNB": "Banking", "INDUSINDBK": "Banking",
    "FEDERALBNK": "Banking", "IDFCFIRSTB": "Banking",
    # NBFC / Finance
    "BAJFINANCE": "NBFC", "BAJAJFINSV": "NBFC", "CHOLAFIN": "NBFC",
    "MUTHOOTFIN": "NBFC", "SUNDARMFIN": "NBFC",
    # Insurance
    "SBILIFE": "Insurance", "HDFCLIFE": "Insurance", "ICICIGI": "Insurance",
    "ICICIPRULI": "Insurance",
    # Energy / Oil & Gas
    "RELIANCE": "Energy", "ONGC": "Energy", "IOC": "Energy",
    "BPCL": "Energy", "GAIL": "Energy", "ATGL": "Energy",
    # Power
    "ADANIGREEN": "Power", "ADANIPOWER": "Power", "ADANIENSOL": "Power",
    "NTPC": "Power", "POWERGRID": "Power", "TATAPOWER": "Power",
    # Ports / Infrastructure
    "ADANIPORTS": "Infrastructure", "ADANIENT": "Infrastructure",
    "LT": "Infrastructure", "NBCC": "Infrastructure",
    # Cement
    "AMBUJACEM": "Cement", "ACC": "Cement", "ULTRACEMCO": "Cement",
    "SHREECEM": "Cement",
    # Healthcare / Pharma
    "APOLLOHOSP": "Healthcare", "SUNPHARMA": "Pharma",
    "DRREDDY": "Pharma", "CIPLA": "Pharma", "DIVISLAB": "Pharma",
    "AUROPHARMA": "Pharma", "ABB": "Pharma",
    # Auto
    "BAJAJ-AUTO": "Auto", "MARUTI": "Auto", "TATAMOTORS": "Auto",
    "M&M": "Auto", "EICHERMOT": "Auto", "HEROMOTOCO": "Auto",
    "TVSMOTOR": "Auto",
    # FMCG / Consumer
    "HINDUNILVR": "FMCG", "ITC": "FMCG", "NESTLEIND": "FMCG",
    "BRITANNIA": "FMCG", "DABUR": "FMCG", "MARICO": "FMCG",
    "GODREJCP": "FMCG", "COLPAL": "FMCG", "TATACONSUM": "FMCG",
    "VBL": "FMCG",
    # Paint
    "ASIANPAINT": "Paint", "BERGEPAINT": "Paint",
    # Telecom
    "BHARTIARTL": "Telecom",
    # Metals / Mining
    "TATASTEEL": "Metals", "JSWSTEEL": "Metals", "HINDALCO": "Metals",
    "COALINDIA": "Metals", "VEDL": "Metals", "SAIL": "Metals",
    "NMDC": "Metals",
    # Holding / Conglomerate
    "ADANIENT": "Conglomerate",
    # Retail
    "DMART": "Retail",
    # Real Estate
    "DLF": "Real Estate", "LODHA": "Real Estate",
    # Capital Goods
    "SIEMENS": "Capital Goods", "HAVELLS": "Capital Goods",
    "CGPOWER": "Capital Goods",
    # Others
    "ZOMATO": "Internet", "PAYTM": "Internet",
    "INDIGO": "Aviation", "IRCTC": "Travel",
    "LTF": "NBFC", "JIOFIN": "NBFC",
    # Defence / Aerospace
    "BEL": "Defence", "HAL": "Defence", "BHEL": "Capital Goods",

    # Finance / NBFC
    "IRFC": "NBFC", "PFC": "NBFC", "RECLTD": "NBFC",
    "SHRIRAMFIN": "NBFC", "LICI": "Insurance",

    # Holding
    "BAJAJHLDNG": "Conglomerate", "GRASIM": "Conglomerate",

    # Metals
    "JINDALSTEL": "Metals", "JSWENERGY": "Power",
    "NHPC": "Power",

    # Consumer / Retail
    "TITAN": "Consumer Goods", "TRENT": "Retail",
    "PIDILITIND": "Consumer Goods",

    # Auto Ancillary
    "MOTHERSON": "Auto",

    # Pharma
    "TORNTPHARM": "Pharma",

    # Internet
    "NAUKRI": "Internet",

    # Auto ancillary
    "BOSCHLTD": "Auto",
}


# ─────────────────────────────────────────────
# 1. YEAR STANDARDIZATION
# ─────────────────────────────────────────────
def standardize_year(val):
    """
    Koi bhi year format lo — standard 'Mar 2024' format mein do.

    Examples:
        'Mar-13'   → 'Mar 2013'
        'Mar-2013' → 'Mar 2013'
        'Mar 2013' → 'Mar 2013'  (already clean)
        '2013'     → 'Mar 2013'  (balancesheet mein sirf year hota hai)
        'TTM'      → 'TTM'
    """
    if pd.isna(val):
        return None

    val = str(val).strip()

    if val.upper() == "TTM":
        return "TTM"

    # Already clean format: 'Mar 2024'
    if re.match(r"^[A-Za-z]{3} \d{4}$", val):
        return val

    # Format: 'Mar-24' or 'Mar-2024'
    m = re.match(r"^([A-Za-z]{3})-(\d{2,4})$", val)
    if m:
        month = m.group(1).capitalize()
        year  = m.group(2)
        if len(year) == 2:
            year = "20" + year if int(year) <= 30 else "19" + year
        return f"{month} {year}"

    # Format: only year like '2013' (balancesheet table)
    if re.match(r"^\d{4}$", val):
        return f"Mar {val}"

    return val  # jo samajh nahi aaya wo as-is rakho


def get_fiscal_year(standardized_year):
    """'Mar 2024' → 2024"""
    if standardized_year == "TTM":
        return 9999
    m = re.search(r"\d{4}", str(standardized_year))
    return int(m.group()) if m else None


def get_sort_order(standardized_year):
    """Sorting ke liye integer. TTM sabse aage."""
    if standardized_year == "TTM":
        return 99999
    fy = get_fiscal_year(standardized_year)
    return fy if fy else 0


# ─────────────────────────────────────────────
# 2. ANALYSIS TABLE PARSER
# ─────────────────────────────────────────────
def parse_analysis_value(val):
    """
    '10 Years: 21%'  → period='10Y', value=21.0
    '5 Years:  8%'   → period='5Y',  value=8.0
    '3 Years: -2%'   → period='3Y',  value=-2.0
    'TTM'            → period='TTM', value=None
    """
    if pd.isna(val) or str(val).strip() == "":
        return None, None

    val = str(val).strip()

    period_map = {"10": "10Y", "5": "5Y", "3": "3Y"}

    m = re.match(r"(\d+)\s*[Yy]ears?\s*[:\s]+(-?\d+(?:\.\d+)?)\s*%", val)
    if m:
        period = period_map.get(m.group(1), m.group(1) + "Y")
        value  = float(m.group(2))
        return period, value

    if "TTM" in val.upper():
        num = re.search(r"(-?\d+(?:\.\d+)?)\s*%", val)
        return "TTM", float(num.group(1)) if num else None

    return None, None


def clean_analysis(df):
    """
    Analysis table ko wide format se long format mein badlo.
    1 row per company per period.
    """
    rows = []
    metric_cols = {
        "compounded_sales_growth":   "compounded_sales_growth_pct",
        "compounded_profit_growth":  "compounded_profit_growth_pct",
        "stock_price_cagr":          "stock_price_cagr_pct",
        "roe":                       "roe_pct",
    }

    for _, row in df.iterrows():
        company = row["company_id"]
        periods = {}

        for raw_col, clean_col in metric_cols.items():
            if raw_col not in df.columns:
                continue
            period, value = parse_analysis_value(row[raw_col])
            if period:
                if period not in periods:
                    periods[period] = {"company_id": company, "period_label": period}
                periods[period][clean_col] = value

        rows.extend(periods.values())

    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 3. COMPUTED COLUMNS
# ─────────────────────────────────────────────
def add_balancesheet_computed(df):
    """debt_to_equity aur equity_ratio compute karo."""
    df = df.copy()
    equity = df["equity_capital"].fillna(0) + df["reserves"].fillna(0)

    # Divide by zero se bachne ke liye
    df["debt_to_equity"] = df["borrowings"] / equity.replace(0, np.nan)
    df["debt_to_equity"] = df["debt_to_equity"].round(2)

    df["equity_ratio"] = equity / df["total_assets"].replace(0, np.nan)
    df["equity_ratio"] = df["equity_ratio"].round(4)

    return df


def add_profitloss_computed(df):
    """Net profit margin, expense ratio, interest coverage compute karo."""
    df = df.copy()

    df["net_profit_margin_pct"] = (
        df["net_profit"] / df["sales"].replace(0, np.nan) * 100
    ).round(2)

    df["expense_ratio_pct"] = (
        df["expenses"] / df["sales"].replace(0, np.nan) * 100
    ).round(2)

    df["interest_coverage"] = (
        df["operating_profit"] / df["interest"].replace(0, np.nan)
    ).round(2)

    return df


def add_cashflow_computed(df):
    """Free cash flow compute karo."""
    df = df.copy()
    df["free_cash_flow"] = (
        df["operating_activity"].fillna(0) + df["investing_activity"].fillna(0)
    )
    return df


# ─────────────────────────────────────────────
# 4. MAIN CLEANING FUNCTIONS PER TABLE
# ─────────────────────────────────────────────
def clean_companies(df):
    print("  → Cleaning companies...")
    df = df.copy()
    df["company_name"] = df["company_name"].str.strip()
    df["sector"] = df["id"].map(SECTOR_MAP).fillna("Other")
    return df


def clean_balancesheet(df):
    print("  → Cleaning balancesheet...")
    df = df.copy()
    df["year"]         = df["year"].apply(standardize_year)
    df["fiscal_year"]  = df["year"].apply(get_fiscal_year)
    df["sort_order"]   = df["year"].apply(get_sort_order)
    df = add_balancesheet_computed(df)
    return df


def clean_cashflow(df):
    print("  → Cleaning cashflow...")
    df = df.copy()
    df["year"]        = df["year"].apply(standardize_year)
    df["fiscal_year"] = df["year"].apply(get_fiscal_year)
    df["sort_order"]  = df["year"].apply(get_sort_order)
    df = add_cashflow_computed(df)
    return df


def clean_profitloss(df):
    print("  → Cleaning profitandloss...")
    df = df.copy()
    df["year"]        = df["year"].apply(standardize_year)
    df["fiscal_year"] = df["year"].apply(get_fiscal_year)
    df["sort_order"]  = df["year"].apply(get_sort_order)
    df = add_profitloss_computed(df)
    return df


def clean_documents(df):
    print("  → Cleaning documents...")
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    return df


def clean_prosandcons(df):
    print("  → Cleaning prosandcons...")
    df = df.copy()
    # Pros aur cons ko separate rows mein todna
    rows = []
    for _, row in df.iterrows():
        if pd.notna(row.get("pros")) and str(row["pros"]).strip() not in ("", "nan"):
            rows.append({
                "company_id": row["company_id"],
                "is_pro":     True,
                "text":       str(row["pros"]).strip()
            })
        if pd.notna(row.get("cons")) and str(row["cons"]).strip() not in ("", "nan"):
            rows.append({
                "company_id": row["company_id"],
                "is_pro":     False,
                "text":       str(row["cons"]).strip()
            })
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 5. RUN ALL
# ─────────────────────────────────────────────
def run_cleaning():
    os.makedirs(CLEAN_DIR, exist_ok=True)

    print("=" * 50)
    print("ETL Step 02 — Clean and Transform")
    print("=" * 50)

    tasks = [
        ("companies.csv",     clean_companies,  "companies.csv"),
        ("balancesheet.csv",  clean_balancesheet, "balancesheet.csv"),
        ("cashflow.csv",      clean_cashflow,   "cashflow.csv"),
        ("profitandloss.csv", clean_profitloss, "profitandloss.csv"),
        ("documents.csv",     clean_documents,  "documents.csv"),
        ("prosandcons.csv",   clean_prosandcons,"prosandcons.csv"),
    ]

    for raw_file, clean_fn, out_file in tasks:
        print(f"\n{'='*50}")
        print(f"Processing: {raw_file}")

        raw_path   = os.path.join(RAW_DIR, raw_file)
        clean_path = os.path.join(CLEAN_DIR, out_file)

        df = pd.read_csv(raw_path)
        df_clean = clean_fn(df)
        df_clean.to_csv(clean_path, index=False)
        print(f"  Rows : {len(df)} → {len(df_clean)}")
        print(f"  Cols : {len(df.columns)} → {len(df_clean.columns)}")
        print(f"  Saved: {clean_path}")

    # Analysis alag handle karo
    print(f"\n{'='*50}")
    print("Processing: analysis.csv (special parsing)")
    df_analysis = pd.read_csv(os.path.join(RAW_DIR, "analysis.csv"))
    df_analysis_clean = clean_analysis(df_analysis)
    df_analysis_clean.to_csv(os.path.join(CLEAN_DIR, "analysis.csv"), index=False)
    print(f"  Rows : {len(df_analysis)} → {len(df_analysis_clean)}")
    print(f"  Saved: {CLEAN_DIR}/analysis.csv")
    print(f"\n  Sample output:")
    print(df_analysis_clean.head(6).to_string(index=False))

    print(f"\n{'='*50}")
    print(" Cleaning complete! Files saved in 'data/clean/'")


if __name__ == "__main__":
    run_cleaning()