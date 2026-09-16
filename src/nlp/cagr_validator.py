import sqlite3
from pathlib import Path

import pandas as pd


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

DB_FILE = BASE_DIR / "data" / "nifty100.db"
PARSED_FILE = BASE_DIR / "output" / "analysis_parsed.csv"
OUTPUT_FILE = BASE_DIR / "output" / "cagr_cross_validation.csv"


# ============================================================
# CONFIGURATION
# ============================================================

DIVERGENCE_THRESHOLD = 5.0

# Parsed analysis metric -> Ratio Engine column by period
CAGR_MAPPING = {
    "compounded_sales_growth": {
        3: "revenue_cagr_3yr",
        5: "revenue_cagr_5yr",
        10: "revenue_cagr_10yr",
    },
    "compounded_profit_growth": {
        3: "pat_cagr_3yr",
        5: "pat_cagr_5yr",
        10: "pat_cagr_10yr",
    },
}


# ============================================================
# LOAD DATA
# ============================================================

def load_parsed_data():
    if not PARSED_FILE.exists():
        raise FileNotFoundError(
            f"Parsed file not found: {PARSED_FILE}"
        )

    return pd.read_csv(PARSED_FILE)


def load_ratio_data():
    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_FILE}"
        )

    conn = sqlite3.connect(DB_FILE)

    query = """
        SELECT
            company_id,
            year,
            revenue_cagr_3yr,
            revenue_cagr_5yr,
            revenue_cagr_10yr,
            pat_cagr_3yr,
            pat_cagr_5yr,
            pat_cagr_10yr
        FROM financial_ratios
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


# ============================================================
# FIND BEST RATIO ENGINE YEAR
# ============================================================

def find_ratio_value(
    ratio_df,
    company_id,
    metric_column,
):
    """
    Find the most recent non-null Ratio Engine value
    for a company and a specific CAGR metric.
    """

    company_rows = ratio_df[
        ratio_df["company_id"] == company_id
    ].copy()

    if company_rows.empty:
        return None, None

    company_rows = company_rows.dropna(
        subset=[metric_column]
    )

    if company_rows.empty:
        return None, None

    company_rows = company_rows.sort_values("year")

    latest = company_rows.iloc[-1]

    return latest[metric_column], int(latest["year"])


# ============================================================
# CROSS VALIDATION
# ============================================================

def validate_cagrs(parsed_df, ratio_df):

    results = []

    cagr_metrics = [
        "compounded_sales_growth",
        "compounded_profit_growth",
    ]

    for _, row in parsed_df.iterrows():

        metric_type = row["metric_type"]

        if metric_type not in cagr_metrics:
            continue

        period = int(row["period_years"])
        company_id = row["company_id"]
        parsed_value = float(row["value_pct"])

        # Only 3, 5 and 10 year CAGR values can be
        # cross-validated against Ratio Engine.
        if period not in CAGR_MAPPING[metric_type]:
            continue

        ratio_column = CAGR_MAPPING[
            metric_type
        ][period]

        ratio_value, ratio_year = find_ratio_value(
            ratio_df,
            company_id,
            ratio_column,
        )

        if ratio_value is None:

            results.append({
                "company_id": company_id,
                "metric_type": metric_type,
                "period_years": period,
                "parsed_value_pct": parsed_value,
                "ratio_engine_value_pct": None,
                "divergence_pct_points": None,
                "threshold_pct_points": DIVERGENCE_THRESHOLD,
                "status": "NO_RATIO_VALUE",
                "ratio_engine_year": None,
            })

            continue

        divergence = abs(
            parsed_value - float(ratio_value)
        )

        if divergence > DIVERGENCE_THRESHOLD:
            status = "DIVERGENCE_GT_5"
        else:
            status = "MATCH"

        results.append({
            "company_id": company_id,
            "metric_type": metric_type,
            "period_years": period,
            "parsed_value_pct": parsed_value,
            "ratio_engine_value_pct": round(
                float(ratio_value), 4
            ),
            "divergence_pct_points": round(
                divergence, 4
            ),
            "threshold_pct_points": DIVERGENCE_THRESHOLD,
            "status": status,
            "ratio_engine_year": ratio_year,
        })

    return pd.DataFrame(results)


# ============================================================
# SAVE OUTPUT
# ============================================================

def save_results(results_df):

    OUTPUT_FILE.parent.mkdir(
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

def print_summary(results_df):

    print()
    print("=" * 60)
    print("CAGR CROSS-VALIDATION SUMMARY")
    print("=" * 60)

    print(
        f"Comparisons performed: {len(results_df)}"
    )

    if results_df.empty:
        print("No 3/5/10-year CAGR values available for validation.")
        return

    matches = (
        results_df["status"] == "MATCH"
    ).sum()

    divergences = (
        results_df["status"] == "DIVERGENCE_GT_5"
    ).sum()

    missing = (
        results_df["status"] == "NO_RATIO_VALUE"
    ).sum()

    print(f"Matches: {matches}")
    print(f"Divergence >5 percentage points: {divergences}")
    print(f"No Ratio Engine value: {missing}")

    print()
    print("Status breakdown:")
    print(
        results_df["status"]
        .value_counts()
        .to_string()
    )

    if divergences > 0:

        print()
        print("DIVERGENCES FOUND:")
        print(
            results_df[
                results_df["status"] == "DIVERGENCE_GT_5"
            ].to_string(index=False)
        )

    print()
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("NLP CAGR CROSS-VALIDATION")
    print("=" * 60)

    parsed_df = load_parsed_data()
    ratio_df = load_ratio_data()

    print(
        f"Parsed analysis rows loaded: {len(parsed_df)}"
    )

    print(
        f"Ratio Engine rows loaded: {len(ratio_df)}"
    )

    results_df = validate_cagrs(
        parsed_df,
        ratio_df
    )

    save_results(results_df)

    print_summary(results_df)

    print()
    print(f"Created: {OUTPUT_FILE}")
    print()
    print("CAGR CROSS-VALIDATION COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()