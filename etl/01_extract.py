"""
ETL Script 01 — Extract
Excel files se data padhke raw CSVs banao
"""

import pandas as pd
import os

RAW_DIR = "data/raw"
OUT_DIR = "data/raw"

# Sector mapping
SECTOR_MAP = {
    "ABB": "Industrials", "ADANIENSOL": "Energy", "ADANIENT": "Conglomerate",
    "ADANIGREEN": "Energy", "ADANIPORTS": "Infrastructure", "ADANIPOWER": "Energy",
    "AMBUJACEM": "Cement", "APOLLOHOSP": "Healthcare", "APOLLOTYRE": "Auto",
    "ASIANPAINT": "Chemicals", "ATGL": "Energy", "AUBANK": "Banking",
    "AXISBANK": "Banking", "BAJAJ-AUTO": "Auto", "BAJAJFINSV": "Financial Services",
    "BAJFINANCE": "Financial Services", "BEL": "Defence", "BHEL": "Industrials",
    "BPCL": "Oil & Gas", "BRITANNIA": "FMCG", "CANBK": "Banking",
    "CHOLAFIN": "Financial Services", "CIPLA": "Pharmaceuticals", "COALINDIA": "Mining",
    "COLPAL": "FMCG", "DLF": "Real Estate", "DIVISLAB": "Pharmaceuticals",
    "DRREDDY": "Pharmaceuticals", "EICHERMOT": "Auto", "ETERNAL": "Technology",
    "GAIL": "Oil & Gas", "GRASIM": "Conglomerate", "HCLTECH": "IT",
    "HDFCBANK": "Banking", "HDFCLIFE": "Insurance", "HEROMOTOCO": "Auto",
    "HINDALCO": "Metals", "HINDUNILVR": "FMCG", "ICICIBANK": "Banking",
    "ICICIGI": "Insurance", "ICICIPRULI": "Insurance", "INDHOTEL": "Hospitality",
    "INDUSINDBK": "Banking", "INDUSTOWER": "Telecom", "INFY": "IT",
    "IOC": "Oil & Gas", "IRCTC": "Travel & Tourism", "IRFC": "Financial Services",
    "ITC": "FMCG", "JINDALSTEL": "Metals", "JIOFIN": "Financial Services",
    "JSWENERGY": "Energy", "JSWSTEEL": "Metals", "KOTAKBANK": "Banking",
    "LICI": "Insurance", "LT": "Industrials", "LTIM": "IT",
    "LTTS": "IT", "M&M": "Auto", "MARICO": "FMCG",
    "MARUTI": "Auto", "MAXHEALTH": "Healthcare", "MOTHERSON": "Auto",
    "MPHASIS": "IT", "NESTLEIND": "FMCG", "NHPC": "Energy",
    "NTPC": "Energy", "NYKAA": "Retail", "ONGC": "Oil & Gas",
    "PAGEIND": "Retail", "PAYTM": "Technology", "PERSISTENT": "IT",
    "PETRONET": "Oil & Gas", "PIDILITIND": "Chemicals", "PNB": "Banking",
    "POLICYBZR": "Technology", "POWERGRID": "Energy", "RELIANCE": "Conglomerate",
    "SAIL": "Metals", "SBICARD": "Financial Services", "SBILIFE": "Insurance",
    "SBIN": "Banking", "SHRIRAMFIN": "Financial Services", "SIEMENS": "Industrials",
    "SUNPHARMA": "Pharmaceuticals", "TATACONSUM": "FMCG", "TATAMOTORS": "Auto",
    "TATAPOWER": "Energy", "TATASTEEL": "Metals", "TCS": "IT",
    "TECHM": "IT", "TIINDIA": "Industrials", "TITAN": "Retail",
    "TORNTPHARM": "Pharmaceuticals", "TRENT": "Retail", "ULTRACEMCO": "Cement",
    "VBL": "FMCG", "VEDL": "Metals", "WIPRO": "IT", "ZOMATO": "Technology"
}

def extract_companies():
    df = pd.read_excel(f"{RAW_DIR}/companies.xlsx", header=1)
    df = df.rename(columns={"id": "symbol"})
    df["sector"] = df["symbol"].map(SECTOR_MAP)
    df.to_csv(f"{OUT_DIR}/companies_raw.csv", index=False)
    print(f"companies → {len(df)} rows")

def extract_profit_loss():
    df = pd.read_excel(f"{RAW_DIR}/profitandloss.xlsx", header=1)
    df = df.rename(columns={"company_id": "symbol"})
    df.to_csv(f"{OUT_DIR}/profitloss_raw.csv", index=False)
    print(f"profit_loss → {len(df)} rows")

def extract_balance_sheet():
    df = pd.read_excel(f"{RAW_DIR}/balancesheet.xlsx", header=1)
    df = df.rename(columns={"company_id": "symbol"})
    df.to_csv(f"{OUT_DIR}/balancesheet_raw.csv", index=False)
    print(f"balance_sheet → {len(df)} rows")

def extract_cash_flow():
    df = pd.read_excel(f"{RAW_DIR}/cashflow.xlsx", header=1)
    df = df.rename(columns={"company_id": "symbol"})
    df.to_csv(f"{OUT_DIR}/cashflow_raw.csv", index=False)
    print(f"cash_flow → {len(df)} rows")

def extract_analysis():
    df = pd.read_excel(f"{RAW_DIR}/analysis.xlsx", header=1)
    df = df.rename(columns={"company_id": "symbol"})
    df.to_csv(f"{OUT_DIR}/analysis_raw.csv", index=False)
    print(f"analysis → {len(df)} rows")

def extract_pros_cons():
    df = pd.read_excel(f"{RAW_DIR}/prosandcons.xlsx", header=1)
    df = df.rename(columns={"company_id": "symbol"})
    df.to_csv(f"{OUT_DIR}/proscons_raw.csv", index=False)
    print(f"pros_cons → {len(df)} rows")

if __name__ == "__main__":
    print("=== Extract Start ===")
    extract_companies()
    extract_profit_loss()
    extract_balance_sheet()
    extract_cash_flow()
    extract_analysis()
    extract_pros_cons()
    print("=== Extract Done ===")