"""
ETL Script 04 — ML Health Scores
==================================
PostgreSQL se data uthata hai, har company ko score karta hai,
aur fact_ml_scores table mein save karta hai.

Usage:
    py -3.11 etl/04_ml_health_scores.py
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
DB_USER     = "postgres"
DB_PASSWORD = "Ronit%40030473"
DB_HOST     = "localhost"
DB_PORT     = "5432"
DB_NAME     = "nifty100"

ENGINE_URL = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_engine():
    return create_engine(ENGINE_URL)


# ─────────────────────────────────────────────
# STEP 1 — DATA LOAD
# ─────────────────────────────────────────────
def load_data(engine):
    """PostgreSQL se saari zaruri tables load karo."""
    print("Loading data from PostgreSQL...")

    pl = pd.read_sql("SELECT * FROM fact_profit_loss", engine)
    bs = pd.read_sql("SELECT * FROM fact_balance_sheet", engine)
    cf = pd.read_sql("SELECT * FROM fact_cash_flow", engine)

    print(f"  Profit & Loss : {len(pl)} rows")
    print(f"  Balance Sheet : {len(bs)} rows")
    print(f"  Cash Flow     : {len(cf)} rows")

    return pl, bs, cf


# ─────────────────────────────────────────────
# STEP 2 — LATEST YEAR KA DATA NIKALO
# ─────────────────────────────────────────────
def get_latest(df):
    """
    Har company ka sirf latest year ka data lo.
    TTM ko prefer karo, warna highest fiscal_year.
    """
    df = df.copy()
    df["fiscal_year"] = pd.to_numeric(df["fiscal_year"], errors="coerce")

    # TTM rows alag karo
    ttm = df[df["year"] == "TTM"].copy()
    non_ttm = df[df["year"] != "TTM"].copy()

    # Non-TTM mein se latest year lo
    latest_non_ttm = (
        non_ttm.sort_values("fiscal_year", ascending=False)
        .groupby("company_id")
        .first()
        .reset_index()
    )

    # TTM available ho toh woh use karo, warna latest year
    ttm_companies = set(ttm["company_id"].unique())
    result = pd.concat([
        ttm[ttm["company_id"].isin(ttm_companies)],
        latest_non_ttm[~latest_non_ttm["company_id"].isin(ttm_companies)]
    ]).reset_index(drop=True)

    return result


# ─────────────────────────────────────────────
# STEP 3 — SCORE KARO 0 to 100
# ─────────────────────────────────────────────
def normalize(series):
    """
    Series ko 0-100 range mein lao.
    Sabse achha company = 100, sabse kharab = 0.
    """
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - mn) / (mx - mn) * 100).round(2)


def score_profitability(pl_latest):
    """
    Profitability Score — kitna profit kama rahi hai company.
    Metrics: net_profit_margin, opm_percentage, eps
    """
    df = pl_latest.copy()

    s1 = normalize(pd.to_numeric(df["net_profit_margin_pct"], errors="coerce").fillna(0))
    s2 = normalize(pd.to_numeric(df["opm_percentage"], errors="coerce").fillna(0))
    s3 = normalize(pd.to_numeric(df["eps"], errors="coerce").fillna(0))

    df["profitability_score"] = ((s1 * 0.4) + (s2 * 0.4) + (s3 * 0.2)).round(2)
    return df[["company_id", "profitability_score"]]


def score_leverage(bs_latest):
    """
    Leverage Score — kitna debt hai company pe.
    Kam debt = achha = high score.
    """
    df = bs_latest.copy()

    dte = pd.to_numeric(df["debt_to_equity"], errors="coerce").fillna(999)
    eq  = pd.to_numeric(df["equity_ratio"], errors="coerce").fillna(0)

    # Debt to equity mein ulta — kam debt = zyada score
    s1 = 100 - normalize(dte.clip(0, 10))
    s2 = normalize(eq)

    df["leverage_score"] = ((s1 * 0.6) + (s2 * 0.4)).round(2)
    return df[["company_id", "leverage_score"]]


def score_cashflow(cf_latest):
    """
    Cashflow Score — cash generation kitni strong hai.
    """
    df = cf_latest.copy()

    s1 = normalize(pd.to_numeric(df["operating_activity"], errors="coerce").fillna(0))
    s2 = normalize(pd.to_numeric(df["free_cash_flow"], errors="coerce").fillna(0))

    df["cashflow_score"] = ((s1 * 0.6) + (s2 * 0.4)).round(2)
    return df[["company_id", "cashflow_score"]]


def score_growth(pl_latest):
    """
    Growth Score — sales aur profit kitni tezi se badh rahi hai.
    """
    df = pl_latest.copy()

    s1 = normalize(pd.to_numeric(df["sales"], errors="coerce").fillna(0))
    s2 = normalize(pd.to_numeric(df["net_profit"], errors="coerce").fillna(0))

    df["growth_score"] = ((s1 * 0.5) + (s2 * 0.5)).round(2)
    return df[["company_id", "growth_score"]]


# ─────────────────────────────────────────────
# STEP 4 — HEALTH LABEL
# ─────────────────────────────────────────────
def get_health_label(score):
    """Overall score ko label mein badlo."""
    if score >= 80:
        return "EXCELLENT"
    elif score >= 60:
        return "GOOD"
    elif score >= 40:
        return "AVERAGE"
    elif score >= 20:
        return "WEAK"
    else:
        return "POOR"


# ─────────────────────────────────────────────
# STEP 5 — COMBINE ALL SCORES
# ─────────────────────────────────────────────
def compute_all_scores(pl, bs, cf):
    print("\nComputing scores...")

    pl_latest = get_latest(pl)
    bs_latest = get_latest(bs)
    cf_latest = get_latest(cf)

    # Har dimension ka score
    prof  = score_profitability(pl_latest)
    lev   = score_leverage(bs_latest)
    cash  = score_cashflow(cf_latest)
    growth= score_growth(pl_latest)

    # Sab merge karo company_id pe
    scores = prof.merge(lev,    on="company_id", how="outer")
    scores = scores.merge(cash,  on="company_id", how="outer")
    scores = scores.merge(growth,on="company_id", how="outer")

    # NaN ko 50 se fill karo — neutral score
    for col in ["profitability_score", "leverage_score", "cashflow_score", "growth_score"]:
        scores[col] = scores[col].fillna(50)

    # Overall score — weighted average
    scores["overall_score"] = (
        scores["profitability_score"] * 0.30 +
        scores["leverage_score"]      * 0.25 +
        scores["cashflow_score"]      * 0.25 +
        scores["growth_score"]        * 0.20
    ).round(2)

    # Health label
    scores["health_label"] = scores["overall_score"].apply(get_health_label)
    scores["computed_at"]  = datetime.now()

    print(f"  Scored {len(scores)} companies")
    return scores


# ─────────────────────────────────────────────
# STEP 6 — SAVE TO POSTGRESQL
# ─────────────────────────────────────────────
def save_scores(engine, scores):
    print("\nSaving to PostgreSQL...")

    scores.to_sql(
        name="fact_ml_scores",
        con=engine,
        if_exists="replace",
        index=False,
        method="multi"
    )
    print(f"   fact_ml_scores — {len(scores)} rows saved")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def run():
    print("=" * 50)
    print("ETL Step 04 — ML Health Scores")
    print("=" * 50)

    engine = get_engine()
    pl, bs, cf = load_data(engine)
    scores = compute_all_scores(pl, bs, cf)

    # Results print karo
    print("\n TOP 10 COMPANIES BY HEALTH SCORE:")
    print("-" * 55)
    top10 = scores.nlargest(10, "overall_score")[
        ["company_id", "overall_score", "health_label",
         "profitability_score", "leverage_score", "cashflow_score"]
    ]
    print(top10.to_string(index=False))

    print("\n HEALTH LABEL DISTRIBUTION:")
    print(scores["health_label"].value_counts().to_string())

    save_scores(engine, scores)

    print("\n ML Health Scores complete!")
    engine.dispose()


if __name__ == "__main__":
    run()