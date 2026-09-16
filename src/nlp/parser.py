import re
from pathlib import Path

import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

INPUT_FILE = BASE_DIR / "data" / "analysis.xlsx"

OUTPUT_DIR = BASE_DIR / "output"
PARSED_FILE = OUTPUT_DIR / "analysis_parsed.csv"
FAILURE_FILE = OUTPUT_DIR / "parse_failures.csv"


# ============================================================
# TARGET METRICS
# ============================================================

METRIC_COLUMNS = {
    "compounded_sales_growth": "compounded_sales_growth",
    "compounded_profit_growth": "compounded_profit_growth",
    "stock_price_cagr": "stock_price_cagr",
    "roe": "roe",
}


# ============================================================
# REGEX PATTERNS
# ============================================================

NUMERIC_PATTERN = re.compile(
    r"(\d+)\s*Years?:?\s*(-?\d+(?:\.\d+)?)\s*%"
    r"|"
    r"Last\s+Year:?\s*(-?\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE
)

TTM_PATTERN = re.compile(
    r"TTM\s*:?\s*(-?\d+(?:\.\d+)?)\s*%",
    re.IGNORECASE
)


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(value):
    """Convert an Excel cell value into clean text."""

    if pd.isna(value):
        return ""

    text = str(value)

    text = re.sub(r"\s+", " ", text).strip()

    return text


# ============================================================
# METRIC PARSER
# ============================================================

def parse_metric_text(text):
    """
    Extract period and percentage from text.

    Examples:
        10 Years: 21%  -> (10, 21.0)
        5 Years: 24%   -> (5, 24.0)
        3 Years: 17%   -> (3, 17.0)
        1 Year: -2%    -> (1, -2.0)
        Last Year: 12% -> (1, 12.0)
        TTM: 43%       -> (0, 43.0)
    """

    text = clean_text(text)

    if not text:
        return None

    # Normal year formats
    match = NUMERIC_PATTERN.search(text)

    if match:

        # Example: 10 Years: 21%
        if match.group(1) is not None:

            period_years = int(match.group(1))
            value_pct = float(match.group(2))

        # Example: Last Year: 12%
        else:

            period_years = 1
            value_pct = float(match.group(3))

        return period_years, value_pct

    # TTM format
    match = TTM_PATTERN.search(text)

    if match:

        value_pct = float(match.group(1))

        # TTM is not a specific number of years.
        # Store as 0.
        return 0, value_pct

    return None


# ============================================================
# LOAD EXCEL
# ============================================================

def load_analysis():
    """Load analysis.xlsx using row 2 as the header."""

    return pd.read_excel(
        INPUT_FILE,
        header=1
    )


# ============================================================
# PARSE ANALYSIS DATA
# ============================================================

def parse_analysis():
    """Parse all four target metrics."""

    df = load_analysis()

    required_columns = [
        "company_id"
    ] + list(METRIC_COLUMNS.keys())

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:

        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    parsed_rows = []
    failures = []

    # Process every Excel row
    for _, row in df.iterrows():

        company_id = row["company_id"]

        # Process all four metrics
        for metric_type, column_name in METRIC_COLUMNS.items():

            raw_text = clean_text(
                row[column_name]
            )

            result = parse_metric_text(
                raw_text
            )

            # Parsing failed
            if result is None:

                failures.append({
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "raw_text": raw_text,
                    "reason": "Pattern did not match",
                })

                continue

            # Parsing succeeded
            period_years, value_pct = result

            parsed_rows.append({
                "company_id": company_id,
                "metric_type": metric_type,
                "period_years": period_years,
                "value_pct": value_pct,
            })

    # Create DataFrames with explicit columns.
    # This is important when there are zero failures.
    parsed_df = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ]
    )

    failures_df = pd.DataFrame(
        failures,
        columns=[
            "company_id",
            "metric_type",
            "raw_text",
            "reason",
        ]
    )

    return parsed_df, failures_df


# ============================================================
# SAVE OUTPUTS
# ============================================================

def save_outputs(parsed_df, failures_df):
    """Save parser results to CSV files."""

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    # Save parsed results
    parsed_df.to_csv(
        PARSED_FILE,
        index=False
    )

    # Save failures
    failures_df.to_csv(
        FAILURE_FILE,
        index=False
    )

    # Summary
    print(
        f"Parsed rows: {len(parsed_df)}"
    )

    print(
        f"Parse failures: {len(failures_df)}"
    )

    print(
        f"Companies parsed: "
        f"{parsed_df['company_id'].nunique()}"
    )

    print(
        f"\nCreated: {PARSED_FILE}"
    )

    print(
        f"Created: {FAILURE_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("NLP ANALYSIS TEXT PARSER")
    print("=" * 60)

    parsed_df, failures_df = parse_analysis()

    save_outputs(
        parsed_df,
        failures_df
    )

    print()
    print("PARSER COMPLETED")
    print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()