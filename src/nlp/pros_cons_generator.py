import sqlite3
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_FILE = BASE_DIR / "data" / "nifty100.db"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_FILE = OUTPUT_DIR / "pros_cons_generated.csv"


# ============================================================
# CONFIGURATION
# ============================================================

MIN_CONFIDENCE = 60.0


# ============================================================
# LOAD DATA
# ============================================================

def load_ratio_data():
    """Load the latest financial ratio data for each company."""

    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_FILE}"
        )

    conn = sqlite3.connect(DB_FILE)

    query = """
        SELECT
            company_id,
            year,
            net_profit_margin,
            operating_profit_margin,
            return_on_equity,
            return_on_capital,
            return_on_assets,
            debt_to_equity,
            interest_coverage,
            free_cash_flow,
            revenue_cagr_3yr,
            revenue_cagr_5yr,
            revenue_cagr_10yr,
            pat_cagr_3yr,
            pat_cagr_5yr,
            pat_cagr_10yr,
            high_leverage_flag,
            icr_warning_flag,
            icr_label,
            composite_quality_score
        FROM financial_ratios
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        raise ValueError(
            "financial_ratios table contains no data."
        )

    return df


def get_latest_company_data(df):
    """Keep the latest available row for every company."""

    df = df.sort_values(
        ["company_id", "year"]
    )

    latest = (
        df.groupby("company_id", as_index=False)
        .tail(1)
        .reset_index(drop=True)
    )

    return latest


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_valid(value):
    return pd.notna(value)


def confidence(base, strength=0):
    """
    Return confidence score between 60 and 99.
    """

    score = base + strength

    return round(
        max(MIN_CONFIDENCE, min(99.0, score)),
        1
    )


def add_result(
    results,
    company_id,
    year,
    sentiment,
    rule_id,
    statement,
    conf,
    metric,
    metric_value
):
    results.append({
        "company_id": company_id,
        "year": int(year),
        "sentiment": sentiment,
        "rule_id": rule_id,
        "statement": statement,
        "confidence_score": conf,
        "trigger_metric": metric,
        "trigger_value": metric_value,
    })


# ============================================================
# 12 PRO RULES
# ============================================================

def apply_pro_rules(row, results):

    company = row["company_id"]
    year = row["year"]

    # PRO 01 — Strong ROE
    if is_valid(row["return_on_equity"]) and row["return_on_equity"] >= 15:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_01",
            "Strong return on equity indicates efficient use of shareholder capital.",
            confidence(82, min(row["return_on_equity"] - 15, 10)),
            "return_on_equity",
            row["return_on_equity"]
        )

    # PRO 02 — Excellent ROE
    if is_valid(row["return_on_equity"]) and row["return_on_equity"] >= 25:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_02",
            "ROE above 25% indicates particularly strong profitability on equity.",
            confidence(88, min(row["return_on_equity"] - 25, 8)),
            "return_on_equity",
            row["return_on_equity"]
        )

    # PRO 03 — Strong ROCE
    if is_valid(row["return_on_capital"]) and row["return_on_capital"] >= 15:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_03",
            "Strong ROCE indicates efficient deployment of capital.",
            confidence(82, min(row["return_on_capital"] - 15, 10)),
            "return_on_capital",
            row["return_on_capital"]
        )

    # PRO 04 — Strong ROA
    if is_valid(row["return_on_assets"]) and row["return_on_assets"] >= 5:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_04",
            "Positive return on assets indicates productive use of the asset base.",
            confidence(78, min(row["return_on_assets"] - 5, 10)),
            "return_on_assets",
            row["return_on_assets"]
        )

    # PRO 05 — Revenue growth
    if is_valid(row["revenue_cagr_3yr"]) and row["revenue_cagr_3yr"] >= 10:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_05",
            "Double-digit three-year revenue CAGR indicates strong business growth.",
            confidence(84, min(row["revenue_cagr_3yr"] - 10, 10)),
            "revenue_cagr_3yr",
            row["revenue_cagr_3yr"]
        )

    # PRO 06 — Long-term revenue growth
    if is_valid(row["revenue_cagr_10yr"]) and row["revenue_cagr_10yr"] >= 10:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_06",
            "Double-digit ten-year revenue CAGR demonstrates sustained long-term growth.",
            confidence(90, min(row["revenue_cagr_10yr"] - 10, 8)),
            "revenue_cagr_10yr",
            row["revenue_cagr_10yr"]
        )

    # PRO 07 — PAT growth
    if is_valid(row["pat_cagr_3yr"]) and row["pat_cagr_3yr"] >= 10:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_07",
            "Strong three-year profit CAGR indicates healthy earnings growth.",
            confidence(84, min(row["pat_cagr_3yr"] - 10, 10)),
            "pat_cagr_3yr",
            row["pat_cagr_3yr"]
        )

    # PRO 08 — Long-term PAT growth
    if is_valid(row["pat_cagr_10yr"]) and row["pat_cagr_10yr"] >= 10:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_08",
            "Double-digit ten-year profit CAGR indicates sustained earnings expansion.",
            confidence(90, min(row["pat_cagr_10yr"] - 10, 8)),
            "pat_cagr_10yr",
            row["pat_cagr_10yr"]
        )

    # PRO 09 — Low leverage
    if is_valid(row["debt_to_equity"]) and row["debt_to_equity"] <= 0.5:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_09",
            "Low debt-to-equity indicates a relatively conservative capital structure.",
            confidence(82),
            "debt_to_equity",
            row["debt_to_equity"]
        )

    # PRO 10 — Strong interest coverage
    if is_valid(row["interest_coverage"]) and row["interest_coverage"] >= 5:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_10",
            "Strong interest coverage provides a comfortable buffer for debt servicing.",
            confidence(84),
            "interest_coverage",
            row["interest_coverage"]
        )

    # PRO 11 — Positive free cash flow
    if is_valid(row["free_cash_flow"]) and row["free_cash_flow"] > 0:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_11",
            "Positive free cash flow indicates cash generation after capital expenditure.",
            confidence(80),
            "free_cash_flow",
            row["free_cash_flow"]
        )

    # PRO 12 — Composite quality
    if is_valid(row["composite_quality_score"]) and row["composite_quality_score"] >= 70:
        add_result(
            results,
            company,
            year,
            "PRO",
            "PRO_12",
            "High composite quality score indicates strong overall financial quality.",
            confidence(88),
            "composite_quality_score",
            row["composite_quality_score"]
        )


# ============================================================
# 12 CON RULES
# ============================================================

def apply_con_rules(row, results):

    company = row["company_id"]
    year = row["year"]

    # CON 01 — Weak ROE
    if is_valid(row["return_on_equity"]) and row["return_on_equity"] < 10:
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_01",
            "Low ROE indicates weaker returns generated on shareholder capital.",
            confidence(82),
            "return_on_equity",
            row["return_on_equity"]
        )

    # CON 02 — Weak ROCE
    if is_valid(row["return_on_capital"]) and row["return_on_capital"] < 10:
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_02",
            "Low ROCE indicates relatively weak efficiency in capital deployment.",
            confidence(80),
            "return_on_capital",
            row["return_on_capital"]
        )

    # CON 03 — Weak ROA
    if is_valid(row["return_on_assets"]) and row["return_on_assets"] < 3:
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_03",
            "Low ROA suggests limited profitability relative to the asset base.",
            confidence(78),
            "return_on_assets",
            row["return_on_assets"]
        )

    # CON 04 — Weak revenue growth
    if is_valid(row["revenue_cagr_3yr"]) and row["revenue_cagr_3yr"] < 5:
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_04",
            "Low three-year revenue CAGR indicates subdued recent business growth.",
            confidence(82),
            "revenue_cagr_3yr",
            row["revenue_cagr_3yr"]
        )

    # CON 05 — Negative revenue growth
    if is_valid(row["revenue_cagr_3yr"]) and row["revenue_cagr_3yr"] < 0:
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_05",
            "Negative three-year revenue CAGR indicates contraction in the business.",
            confidence(92),
            "revenue_cagr_3yr",
            row["revenue_cagr_3yr"]
        )

    # CON 06 — Weak PAT growth
    if is_valid(row["pat_cagr_3yr"]) and row["pat_cagr_3yr"] < 5:
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_06",
            "Low three-year profit CAGR indicates subdued earnings growth.",
            confidence(82),
            "pat_cagr_3yr",
            row["pat_cagr_3yr"]
        )

    # CON 07 — Negative PAT growth
    if is_valid(row["pat_cagr_3yr"]) and row["pat_cagr_3yr"] < 0:
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_07",
            "Negative three-year profit CAGR indicates earnings contraction.",
            confidence(92),
            "pat_cagr_3yr",
            row["pat_cagr_3yr"]
        )

    # CON 08 — High leverage
    if (
        is_valid(row["debt_to_equity"])
        and row["debt_to_equity"] > 1
    ):
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_08",
            "High debt-to-equity indicates elevated financial leverage.",
            confidence(86),
            "debt_to_equity",
            row["debt_to_equity"]
        )

    # CON 09 — Weak interest coverage
    if (
        is_valid(row["interest_coverage"])
        and row["interest_coverage"] < 2
    ):
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_09",
            "Low interest coverage indicates a smaller buffer for servicing interest obligations.",
            confidence(88),
            "interest_coverage",
            row["interest_coverage"]
        )

    # CON 10 — Negative free cash flow
    if (
        is_valid(row["free_cash_flow"])
        and row["free_cash_flow"] < 0
    ):
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_10",
            "Negative free cash flow indicates cash outflow after capital expenditure.",
            confidence(86),
            "free_cash_flow",
            row["free_cash_flow"]
        )

    # CON 11 — High leverage flag
    if (
        is_valid(row["high_leverage_flag"])
        and row["high_leverage_flag"] == 1
    ):
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_11",
            "The financial model identifies the company as highly leveraged.",
            confidence(94),
            "high_leverage_flag",
            row["high_leverage_flag"]
        )

    # CON 12 — ICR warning
    if (
        is_valid(row["icr_warning_flag"])
        and row["icr_warning_flag"] == 1
    ):
        add_result(
            results,
            company,
            year,
            "CON",
            "CON_12",
            "The interest coverage warning flag indicates potential debt-servicing pressure.",
            confidence(94),
            "icr_warning_flag",
            row["icr_warning_flag"]
        )


# ============================================================
# FALLBACK RULES
# ============================================================

def ensure_minimum_pro(row, results):

    company = row["company_id"]
    year = row["year"]

    company_pros = [
        x for x in results
        if x["company_id"] == company
        and x["sentiment"] == "PRO"
    ]

    if company_pros:
        return

    # Fallback based on the strongest available metric
    if is_valid(row["return_on_equity"]):
        metric = "return_on_equity"
        value = row[metric]
        statement = (
            "Return on equity provides a measurable indicator "
            "of shareholder capital efficiency."
        )
    elif is_valid(row["revenue_cagr_3yr"]):
        metric = "revenue_cagr_3yr"
        value = row[metric]
        statement = (
            "The company has measurable three-year revenue "
            "growth data available for evaluation."
        )
    else:
        metric = "composite_quality_score"
        value = row["composite_quality_score"]
        statement = (
            "The company has a measurable composite financial "
            "quality score available for evaluation."
        )

    add_result(
        results,
        company,
        year,
        "PRO",
        "PRO_FALLBACK",
        statement,
        60.0,
        metric,
        value
    )


def ensure_minimum_con(row, results):

    company = row["company_id"]
    year = row["year"]

    company_cons = [
        x for x in results
        if x["company_id"] == company
        and x["sentiment"] == "CON"
    ]

    if company_cons:
        return

    add_result(
        results,
        company,
        year,
        "CON",
        "CON_FALLBACK",
        "The available financial metrics should be monitored for potential weaknesses.",
        60.0,
        "financial_metrics",
        None
    )


# ============================================================
# GENERATOR
# ============================================================

def generate_pros_cons(df):

    results = []

    for _, row in df.iterrows():

        apply_pro_rules(row, results)
        apply_con_rules(row, results)

        ensure_minimum_pro(row, results)
        ensure_minimum_con(row, results)

    return pd.DataFrame(results)


# ============================================================
# SAVE
# ============================================================

def save_results(results_df):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    results_df.to_csv(
        OUTPUT_FILE,
        index=False
    )


# ============================================================
# SUMMARY
# ============================================================

def print_summary(results_df, company_df):

    print()
    print("=" * 60)
    print("PROS / CONS GENERATOR SUMMARY")
    print("=" * 60)

    print(
        f"Companies processed: {len(company_df)}"
    )

    print(
        f"Total insights generated: {len(results_df)}"
    )

    print(
        f"Pros generated: "
        f"{(results_df.sentiment == 'PRO').sum()}"
    )

    print(
        f"Cons generated: "
        f"{(results_df.sentiment == 'CON').sum()}"
    )

    print()
    print("Rule usage:")
    print(
        results_df["rule_id"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print()
    print("Confidence summary:")

    print(
        results_df["confidence_score"]
        .describe()
        .round(2)
        .to_string()
    )

    print()
    print("Companies with at least 1 PRO:")

    pro_counts = (
        results_df[
            results_df["sentiment"] == "PRO"
        ]
        .groupby("company_id")
        .size()
    )

    print(
        f"{len(pro_counts)} / {len(company_df)}"
    )

    print()
    print("Companies with at least 1 CON:")

    con_counts = (
        results_df[
            results_df["sentiment"] == "CON"
        ]
        .groupby("company_id")
        .size()
    )

    print(
        f"{len(con_counts)} / {len(company_df)}"
    )

    print()
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("NLP PROS / CONS GENERATOR")
    print("=" * 60)

    ratio_df = load_ratio_data()

    company_df = get_latest_company_data(
        ratio_df
    )

    print(
        f"Latest company records: {len(company_df)}"
    )

    results_df = generate_pros_cons(
        company_df
    )

    save_results(
        results_df
    )

    print_summary(
        results_df,
        company_df
    )

    print()
    print(f"Created: {OUTPUT_FILE}")

    print()
    print("PROS / CONS GENERATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()