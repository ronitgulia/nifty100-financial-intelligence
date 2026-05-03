"""
ETL Script 04 — ML Health Scores
Har company ka health score calculate karo (0-100)
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime

DB_USER     = "postgres"
DB_PASSWORD = "Ronit%40030473"
DB_HOST     = "localhost"
DB_PORT     = "5432"
DB_NAME     = "bluestock_dw"

ENGINE_URL = f"postgresql+pg8000://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def get_engine():
    return create_engine(ENGINE_URL)


def load_data(engine):
    pl  = pd.read_sql("SELECT * FROM fact_profit_loss",  engine)
    bs  = pd.read_sql("SELECT * FROM fact_balance_sheet", engine)
    cf  = pd.read_sql("SELECT * FROM fact_cash_flow",     engine)
    an  = pd.read_sql("SELECT * FROM fact_analysis",      engine)
    return pl, bs, cf, an


def score_profitability(pl):
    """OPM% aur net profit margin ke basis pe score"""
    latest = pl.sort_values("year").groupby("symbol").last().reset_index()
    latest["npm"] = latest["net_profit"] / latest["sales"] * 100

    scores = pd.DataFrame()
    scores["symbol"] = latest["symbol"]

    # OPM score (0-40 points)
    scores["opm_score"] = latest["opm_pct"].clip(0, 40)

    # Net profit margin score (0-30 points)
    scores["npm_score"] = latest["npm"].clip(0, 30)

    scores["profitability_score"] = (scores["opm_score"] + scores["npm_score"]).clip(0, 100)
    return scores[["symbol", "profitability_score"]]


def score_growth(pl):
    """Sales growth ke basis pe score"""
    pl = pl.sort_values(["symbol", "year"])

    def cagr_score(group):
        group = group.dropna(subset=["sales"])
        if len(group) < 3:
            return 50.0
        first = group["sales"].iloc[0]
        last  = group["sales"].iloc[-1]
        years = len(group) - 1
        if first <= 0:
            return 50.0
        cagr = ((last / first) ** (1 / years) - 1) * 100
        return float(np.clip(cagr * 3, 0, 100))

    growth = pl.groupby("symbol").apply(cagr_score).reset_index()
    growth.columns = ["symbol", "growth_score"]
    return growth


def score_leverage(bs):
    """Debt to Equity ke basis pe score — kam debt = zyada score"""
    latest = bs.sort_values("year").groupby("symbol").last().reset_index()

    def de_score(de):
        if pd.isna(de) or de < 0:
            return 70.0
        if de == 0:
            return 100.0
        if de < 0.5:
            return 90.0
        if de < 1.0:
            return 75.0
        if de < 2.0:
            return 50.0
        if de < 3.0:
            return 25.0
        return 10.0

    latest["leverage_score"] = latest["debt_to_equity"].apply(de_score)
    return latest[["symbol", "leverage_score"]]


def score_cashflow(cf, pl):
    """Operating cash flow vs net profit ke basis pe score"""
    latest_cf = cf.sort_values("year").groupby("symbol").last().reset_index()
    latest_pl = pl.sort_values("year").groupby("symbol").last().reset_index()

    merged = latest_cf.merge(latest_pl[["symbol", "net_profit"]], on="symbol", how="left")

    def cf_score(row):
        if pd.isna(row["operating_activity"]) or pd.isna(row["net_profit"]):
            return 50.0
        if row["net_profit"] == 0:
            return 50.0
        ratio = row["operating_activity"] / row["net_profit"]
        if ratio >= 1.2:
            return 100.0
        if ratio >= 1.0:
            return 85.0
        if ratio >= 0.7:
            return 65.0
        if ratio >= 0.5:
            return 45.0
        return 20.0

    merged["cashflow_score"] = merged.apply(cf_score, axis=1)
    return merged[["symbol", "cashflow_score"]]


def score_consistency(pl):
    """Kitne saal company profitable rahi"""
    def consistency(group):
        profitable_years = (group["net_profit"] > 0).sum()
        total_years      = len(group)
        if total_years == 0:
            return 50.0
        return float((profitable_years / total_years) * 100)

    cons = pl.groupby("symbol").apply(consistency).reset_index()
    cons.columns = ["symbol", "consistency_score"]
    return cons


def get_health_label(score):
    if score >= 85:
        return "EXCELLENT"
    if score >= 70:
        return "GOOD"
    if score >= 50:
        return "AVERAGE"
    if score >= 35:
        return "WEAK"
    return "POOR"


def calculate_scores(engine):
    print("Loading data...")
    pl, bs, cf, an = load_data(engine)

    print("Calculating scores...")
    prof  = score_profitability(pl)
    grow  = score_growth(pl)
    lev   = score_leverage(bs)
    cash  = score_cashflow(cf, pl)
    cons  = score_consistency(pl)

    # Sab merge karo
    scores = prof.merge(grow,  on="symbol", how="outer")
    scores = scores.merge(lev,  on="symbol", how="outer")
    scores = scores.merge(cash, on="symbol", how="outer")
    scores = scores.merge(cons, on="symbol", how="outer")

    # Fill missing
    for col in ["profitability_score", "growth_score", "leverage_score",
                "cashflow_score", "consistency_score"]:
        scores[col] = scores[col].fillna(50.0)

    # Weighted overall score
    scores["overall_score"] = (
        scores["profitability_score"] * 0.30 +
        scores["growth_score"]        * 0.25 +
        scores["leverage_score"]      * 0.20 +
        scores["cashflow_score"]      * 0.15 +
        scores["consistency_score"]   * 0.10
    ).round(2)

    scores["health_label"] = scores["overall_score"].apply(get_health_label)
    scores["computed_at"]  = datetime.now()

    return scores


def run():
    print("=" * 50)
    print("ETL Step 04 — ML Health Scores")
    print("=" * 50)

    engine = get_engine()

    scores = calculate_scores(engine)

    # Database mein load karo
    scores.to_sql("fact_ml_scores", con=engine,
                  if_exists="replace", index=False,
                  method="multi", chunksize=500)

    print(f"\n fact_ml_scores → {len(scores)} rows loaded")

    # Summary print karo
    print(f"\n{'='*50}")
    print("Health Label Distribution:")
    print(f"{'='*50}")
    print(scores["health_label"].value_counts().to_string())

    print(f"\nTop 10 Healthiest Companies:")
    top10 = scores.nlargest(10, "overall_score")[["symbol", "overall_score", "health_label"]]
    print(top10.to_string(index=False))

    engine.dispose()
    print("\n All done!")


if __name__ == "__main__":
    run()