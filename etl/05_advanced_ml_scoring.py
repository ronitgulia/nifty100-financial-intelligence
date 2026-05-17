import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from datetime import datetime
from urllib.parse import quote_plus

password   = quote_plus("Ronit@030473")
ENGINE_URL = f"postgresql+psycopg2://postgres:{password}@localhost:5432/bluestock_dw"


def get_engine():
    return create_engine(ENGINE_URL)


def load_data(engine):
    print("Loading data...")
    pl = pd.read_sql("SELECT * FROM fact_profit_loss", engine)
    bs = pd.read_sql("SELECT * FROM fact_balance_sheet", engine)
    cf = pd.read_sql("SELECT * FROM fact_cash_flow", engine)
    an = pd.read_sql("SELECT * FROM fact_analysis", engine)
    co = pd.read_sql("SELECT * FROM dim_company", engine)
    print(f"  P&L: {len(pl)} | BS: {len(bs)} | CF: {len(cf)} | Analysis: {len(an)}")
    return pl, bs, cf, an, co


def get_latest(df, company_col="symbol"):
    df = df.copy()
    df["fiscal_year"] = pd.to_numeric(df.get("fiscal_year", pd.Series([0]*len(df))), errors="coerce")
    non_ttm = df[df["year"] != "TTM"].copy() if "year" in df.columns else df.copy()
    latest = (
        non_ttm.sort_values("fiscal_year", ascending=False)
        .groupby(company_col)
        .first()
        .reset_index()
    )
    return latest


def get_last_n_years(df, n=5, company_col="symbol"):
    df = df.copy()
    df["fiscal_year"] = pd.to_numeric(df.get("fiscal_year", pd.Series([0]*len(df))), errors="coerce")
    non_ttm = df[df["year"] != "TTM"].copy() if "year" in df.columns else df.copy()
    non_ttm = non_ttm.sort_values("fiscal_year", ascending=False)
    result = non_ttm.groupby(company_col).head(n)
    return result


def normalize(series, higher_is_better=True):
    s = pd.to_numeric(series, errors="coerce")
    s = s.fillna(s.median() if not s.isna().all() else 50)
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series([50.0] * len(s), index=s.index)
    normalized = (s - mn) / (mx - mn) * 100
    if not higher_is_better:
        normalized = 100 - normalized
    return normalized.round(2)


def score_profitability(pl, companies):
    print("  Scoring profitability...")
    latest = get_latest(pl)

    latest["net_profit_margin"] = (
        pd.to_numeric(latest["net_profit"], errors="coerce") /
        pd.to_numeric(latest["sales"], errors="coerce").replace(0, np.nan) * 100
    )

    s1 = normalize(latest["opm_pct"])
    s2 = normalize(latest["net_profit_margin"])
    latest["profitability_score"] = (s1 * 0.5 + s2 * 0.5).round(2)

    result = latest[["symbol", "profitability_score"]].copy()
    result = companies[["symbol"]].merge(result, on="symbol", how="left")
    result["profitability_score"] = result["profitability_score"].fillna(0)
    return result


def score_revenue_growth(an, companies):
    print("  Scoring revenue growth...")

    period_col = "period_label" if "period_label" in an.columns else "period"
    growth_col = "compounded_sales_growth_pct" if "compounded_sales_growth_pct" in an.columns else "compounded_sales_growth"
    symbol_col = "symbol" if "symbol" in an.columns else "company_id"

    growth_3y = an[an[period_col] == "3Y"].copy() if period_col in an.columns else pd.DataFrame()

    if not growth_3y.empty and growth_col in growth_3y.columns:
        growth_3y = growth_3y[[symbol_col, growth_col]].rename(
            columns={symbol_col: "symbol", growth_col: "sales_growth_3y"}
        )
        growth_3y["sales_growth_3y"] = pd.to_numeric(growth_3y["sales_growth_3y"], errors="coerce")
        growth_3y["growth_score_raw"] = growth_3y["sales_growth_3y"].apply(
            lambda x: max(0, x) if not pd.isna(x) else 0
        )
        growth_3y["growth_score"] = normalize(growth_3y["growth_score_raw"])
        result = companies[["symbol"]].merge(
            growth_3y[["symbol", "growth_score"]], on="symbol", how="left"
        )
    else:
        result = companies[["symbol"]].copy()
        result["growth_score"] = 50.0

    result["growth_score"] = result["growth_score"].fillna(50)
    return result


def score_leverage(bs, companies):
    print("  Scoring leverage...")
    latest = get_latest(bs)

    dte = pd.to_numeric(latest["debt_to_equity"], errors="coerce").fillna(999)

    def dte_to_score(x):
        if pd.isna(x) or x > 2:
            return 0
        if x < 0.1:
            return 100
        return round((2 - x) / (2 - 0.1) * 100, 2)

    latest["leverage_score"] = dte.apply(dte_to_score)

    result = latest[["symbol", "leverage_score"]].copy()
    result = companies[["symbol"]].merge(result, on="symbol", how="left")
    result["leverage_score"] = result["leverage_score"].fillna(50)
    return result


def score_cashflow(cf, pl, companies):
    print("  Scoring cash flow...")
    latest_cf = get_latest(cf)
    latest_pl = get_latest(pl)

    merged = latest_cf.merge(
        latest_pl[["symbol", "net_profit"]],
        on="symbol", how="left"
    )

    merged["cash_conversion"] = (
        pd.to_numeric(merged["operating_activity"], errors="coerce") /
        pd.to_numeric(merged["net_profit"], errors="coerce").replace(0, np.nan)
    )

    def ccr_to_score(x):
        if pd.isna(x):
            return 50
        if x >= 1.2:
            return 100
        if x <= 0:
            return 0
        return round(x / 1.2 * 100, 2)

    merged["cashflow_score"] = merged["cash_conversion"].apply(ccr_to_score)

    result = merged[["symbol", "cashflow_score"]].copy()
    result = companies[["symbol"]].merge(result, on="symbol", how="left")
    result["cashflow_score"] = result["cashflow_score"].fillna(50)
    return result


def score_dividend(pl, companies):
    print("  Scoring dividend...")
    last5 = get_last_n_years(pl, n=5)

    div_col = "dividend_payout" if "dividend_payout" in pl.columns else "dividend_payout_pct"

    if div_col in last5.columns:
        last5[div_col] = pd.to_numeric(last5[div_col], errors="coerce").fillna(0)
        summary = last5.groupby("symbol").agg(
            avg_div=(div_col, "mean"),
            years_with_div=(div_col, lambda x: (x > 0).sum()),
            total_years=(div_col, "count")
        ).reset_index()

        def div_to_score(row):
            consistency = row["years_with_div"] / max(row["total_years"], 1)
            avg = row["avg_div"]
            if consistency >= 0.8 and avg >= 30:
                return 100
            if consistency >= 0.6 and avg >= 20:
                return 70
            if consistency >= 0.4:
                return 40
            return 10

        summary["dividend_score"] = summary.apply(div_to_score, axis=1)
        result = companies[["symbol"]].merge(
            summary[["symbol", "dividend_score"]], on="symbol", how="left"
        )
    else:
        result = companies[["symbol"]].copy()
        result["dividend_score"] = 10.0

    result["dividend_score"] = result["dividend_score"].fillna(10)
    return result


def score_growth_trend(pl, companies):
    print("  Scoring growth trend...")
    last5 = get_last_n_years(pl, n=5)
    last5["sales"] = pd.to_numeric(last5["sales"], errors="coerce")
    last5["fiscal_year"] = pd.to_numeric(last5["fiscal_year"], errors="coerce")

    trends = []
    for symbol, group in last5.groupby("symbol"):
        group = group.dropna(subset=["sales", "fiscal_year"])
        if len(group) >= 3:
            try:
                x = group["fiscal_year"].values.astype(float)
                y = group["sales"].values.astype(float)
                # Normalize x to avoid numerical issues
                x = x - x.mean()
                slope = np.polyfit(x, y, 1)[0]
                trends.append({"symbol": symbol, "slope": slope})
            except Exception:
                trends.append({"symbol": symbol, "slope": 0})
        else:
            trends.append({"symbol": symbol, "slope": 0})
    trend_df = pd.DataFrame(trends)
    trend_df["trend_score"] = normalize(trend_df["slope"])

    result = companies[["symbol"]].merge(
        trend_df[["symbol", "trend_score"]], on="symbol", how="left"
    )
    result["trend_score"] = result["trend_score"].fillna(50)
    return result


def compute_final_scores(pl, bs, cf, an, companies):
    print("\nComputing all dimension scores...")

    prof  = score_profitability(pl, companies)
    grow  = score_revenue_growth(an, companies)
    lev   = score_leverage(bs, companies)
    cash  = score_cashflow(cf, pl, companies)
    div   = score_dividend(pl, companies)
    trend = score_growth_trend(pl, companies)

    scores = prof.merge(grow,  on="symbol", how="outer")
    scores = scores.merge(lev,   on="symbol", how="outer")
    scores = scores.merge(cash,  on="symbol", how="outer")
    scores = scores.merge(div,   on="symbol", how="outer")
    scores = scores.merge(trend, on="symbol", how="outer")

    scores["overall_score"] = (
        scores["profitability_score"] * 0.25 +
        scores["growth_score"]        * 0.20 +
        scores["leverage_score"]      * 0.20 +
        scores["cashflow_score"]      * 0.15 +
        scores["dividend_score"]      * 0.10 +
        scores["trend_score"]         * 0.10
    ).round(2)

    def get_label(score):
        if score >= 85: return "EXCELLENT"
        if score >= 70: return "GOOD"
        if score >= 50: return "AVERAGE"
        if score >= 35: return "WEAK"
        return "POOR"

    scores["health_label"] = scores["overall_score"].apply(get_label)
    scores["computed_at"]  = datetime.now()

    return scores


def generate_pros_cons(pl, bs, cf, scores):
    print("\nGenerating auto pros & cons...")
    rows = []

    latest_pl = get_latest(pl)
    latest_bs = get_latest(bs)
    last5_pl  = get_last_n_years(pl, n=5)
    last5_cf  = get_last_n_years(cf, n=5)

    div_col = "dividend_payout" if "dividend_payout" in pl.columns else "dividend_payout_pct"

    for _, score_row in scores.iterrows():
        symbol = score_row["symbol"]

        pl_row = latest_pl[latest_pl["symbol"] == symbol]
        bs_row = latest_bs[latest_bs["symbol"] == symbol]
        pl5    = last5_pl[last5_pl["symbol"] == symbol]
        cf5    = last5_cf[last5_cf["symbol"] == symbol]

        if pl_row.empty or bs_row.empty:
            continue

        dte = pd.to_numeric(bs_row["debt_to_equity"].values[0], errors="coerce")
        if pd.notna(dte) and dte < 0.1:
            rows.append({"symbol": symbol, "is_pro": True,
                         "text": "Company is almost debt free."})

        if score_row.get("profitability_score", 0) > 70:
            rows.append({"symbol": symbol, "is_pro": True,
                         "text": "Company has a good return on equity track record."})

        if div_col in pl5.columns:
            pl5_div = pd.to_numeric(pl5[div_col], errors="coerce").fillna(0)
            avg_div = pl5_div.mean()
            div_years = (pl5_div > 30).sum()
            if div_years >= 3 and avg_div > 30:
                rows.append({"symbol": symbol, "is_pro": True,
                             "text": f"Healthy dividend payout of {avg_div:.1f}% maintained consistently."})

        if score_row.get("growth_score", 0) > 70:
            rows.append({"symbol": symbol, "is_pro": True,
                         "text": "Strong long-term revenue growth track record."})

        if not cf5.empty and not pl5.empty:
            ocf = pd.to_numeric(cf5["operating_activity"], errors="coerce").fillna(0).values
            npt = pd.to_numeric(pl5["net_profit"], errors="coerce").fillna(0).values[:len(ocf)]
            if len(ocf) >= 3 and (ocf > npt).sum() >= 3:
                rows.append({"symbol": symbol, "is_pro": True,
                             "text": "Strong cash conversion — OCF exceeds reported profits."})

        if score_row.get("growth_score", 100) < 40:
            rows.append({"symbol": symbol, "is_pro": False,
                         "text": "Below-average sales growth over past five years."})

        if pd.notna(dte) and dte > 1.5:
            rows.append({"symbol": symbol, "is_pro": False,
                         "text": f"High debt levels — D/E ratio of {dte:.2f} requires monitoring."})

        if score_row.get("cashflow_score", 100) < 40:
            rows.append({"symbol": symbol, "is_pro": False,
                         "text": "Earnings quality concern — cash generation lags reported profits."})

        if not pl_row.empty:
            interest  = pd.to_numeric(pl_row["interest"].values[0], errors="coerce")
            op_profit = pd.to_numeric(pl_row["operating_profit"].values[0], errors="coerce")
            if pd.notna(interest) and pd.notna(op_profit) and interest > 0:
                coverage = op_profit / interest
                if coverage < 2:
                    rows.append({"symbol": symbol, "is_pro": False,
                                 "text": f"Low interest coverage ratio of {coverage:.1f} — debt repayment risk."})

    print(f"  Generated {len(rows)} pros/cons entries")
    return pd.DataFrame(rows)


def save_to_db(engine, scores, pros_cons):
    print("\nSaving to database...")

    scores_to_save = scores[[
        "symbol", "profitability_score", "growth_score",
        "leverage_score", "cashflow_score", "dividend_score",
        "trend_score", "overall_score", "health_label", "computed_at"
    ]].copy()

    scores_to_save.to_sql(
        "fact_ml_scores", engine,
        if_exists="replace", index=False, method="multi", chunksize=500
    )
    print(f"   fact_ml_scores — {len(scores_to_save)} rows saved")

    if not pros_cons.empty:
        pros_cons.to_sql(
            "fact_pros_cons", engine,
            if_exists="replace", index=False, method="multi", chunksize=500
        )
        print(f"   fact_pros_cons — {len(pros_cons)} rows saved")


def run():
    print("=" * 55)
    print("ETL Step 05 — Advanced ML Health Scoring")
    print("=" * 55)

    engine = get_engine()
    pl, bs, cf, an, companies = load_data(engine)
    scores    = compute_final_scores(pl, bs, cf, an, companies)
    pros_cons = generate_pros_cons(pl, bs, cf, scores)
    save_to_db(engine, scores, pros_cons)

    print(f"\n HEALTH LABEL DISTRIBUTION:")
    print(scores["health_label"].value_counts().to_string())

    print(f"\n TOP 5 COMPANIES:")
    top5 = scores.nlargest(5, "overall_score")[["symbol", "overall_score", "health_label"]]
    print(top5.to_string(index=False))

    print(f"\n Advanced ML Scoring complete!")
    engine.dispose()


if __name__ == "__main__":
    run()