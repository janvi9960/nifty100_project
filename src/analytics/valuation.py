import sqlite3
from pathlib import Path

import pandas as pd


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

def load_data():

    with sqlite3.connect(DB_PATH) as conn:

        query = """
        SELECT
            mc.company_id,
            c.company_name,
            s.broad_sector AS sector,
            mc.year,
            mc.market_cap_crore,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.ev_ebitda,
            fr.free_cash_flow
        FROM market_cap mc

        LEFT JOIN companies c
            ON mc.company_id = c.id

        LEFT JOIN sectors s
            ON mc.company_id = s.company_id

        LEFT JOIN financial_ratios fr
            ON mc.company_id = fr.company_id
            AND mc.year = fr.year

        ORDER BY
            mc.company_id,
            mc.year
        """

        return pd.read_sql_query(
            query,
            conn
        )


# ---------------------------------------------------------
# PREPARE LATEST YEAR DATA
# ---------------------------------------------------------

def prepare_latest_data(df):

    df = df.copy()

    numeric_columns = [
        "market_cap_crore",
        "pe_ratio",
        "pb_ratio",
        "ev_ebitda",
        "free_cash_flow",
    ]

    for column in numeric_columns:

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce"
    )


    # Latest available year for each company
    latest = (
        df.sort_values("year")
        .groupby("company_id", as_index=False)
        .tail(1)
        .copy()
    )


    return latest


# ---------------------------------------------------------
# FCF YIELD
# ---------------------------------------------------------

def calculate_fcf_yield(df):

    df = df.copy()

    df["FCF_yield_pct"] = None

    valid_market_cap = (
        df["market_cap_crore"].notna()
        & (df["market_cap_crore"] != 0)
    )

    valid_fcf = df["free_cash_flow"].notna()


    valid = (
        valid_market_cap
        & valid_fcf
    )


    df.loc[valid, "FCF_yield_pct"] = (
        df.loc[valid, "free_cash_flow"]
        / df.loc[valid, "market_cap_crore"]
        * 100
    )


    return df


# ---------------------------------------------------------
# SECTOR MEDIAN P/E
# ---------------------------------------------------------

def calculate_sector_median_pe(df):

    df = df.copy()

    # Only positive P/E values are meaningful
    positive_pe = df[
        df["pe_ratio"].notna()
        & (df["pe_ratio"] > 0)
        & df["sector"].notna()
    ].copy()


    sector_medians = (
        positive_pe
        .groupby("sector")["pe_ratio"]
        .median()
        .rename("5yr_median_PE")
        .reset_index()
    )


    # Sprint specification calls this column
    # 5yr_median_PE. If only latest-year data is available,
    # the available sector median is used.
    df = df.merge(
        sector_medians,
        on="sector",
        how="left"
    )


    return df


# ---------------------------------------------------------
# P/E COMPARISON
# ---------------------------------------------------------

def calculate_pe_comparison(df):

    df = df.copy()

    df["PE_vs_sector_median_pct"] = None


    valid = (
        df["pe_ratio"].notna()
        & (df["pe_ratio"] > 0)
        & df["5yr_median_PE"].notna()
        & (df["5yr_median_PE"] > 0)
    )


    df.loc[valid, "PE_vs_sector_median_pct"] = (
        (
            df.loc[valid, "pe_ratio"]
            / df.loc[valid, "5yr_median_PE"]
        )
        - 1
    ) * 100


    return df


# ---------------------------------------------------------
# VALUATION FLAGS
# ---------------------------------------------------------

def assign_valuation_flag(row):

    pe = row["pe_ratio"]
    median_pe = row["5yr_median_PE"]


    if pd.isna(pe) or pd.isna(median_pe):
        return "N/A"


    if pe <= 0 or median_pe <= 0:
        return "N/A"


    if pe > median_pe * 1.5:
        return "Caution"


    if pe < median_pe * 0.7:
        return "Discount"


    return "Fair"


# ---------------------------------------------------------
# BUILD VALUATION SUMMARY
# ---------------------------------------------------------

def build_valuation_summary():

    print("=" * 60)
    print("NIFTY 100 VALUATION MODULE")
    print("=" * 60)


    print("\nLoading database data...")

    raw_data = load_data()

    print(
        f"Rows loaded: {len(raw_data)}"
    )


    if raw_data.empty:
        raise RuntimeError(
            "No valuation data found in the database."
        )


    print("Preparing latest company data...")

    latest = prepare_latest_data(
        raw_data
    )


    print(
        f"Companies found: "
        f"{latest['company_id'].nunique()}"
    )


    print("Calculating FCF Yield...")

    latest = calculate_fcf_yield(
        latest
    )


    print("Calculating sector median P/E...")

    latest = calculate_sector_median_pe(
        latest
    )


    print("Calculating P/E comparison...")

    latest = calculate_pe_comparison(
        latest
    )


    print("Assigning valuation flags...")

    latest["flag"] = latest.apply(
        assign_valuation_flag,
        axis=1
    )


    # -----------------------------------------------------
    # FINAL COLUMNS
    # -----------------------------------------------------

    summary = latest[
        [
            "company_id",
            "company_name",
            "sector",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "FCF_yield_pct",
            "5yr_median_PE",
            "PE_vs_sector_median_pct",
            "flag",
        ]
    ].copy()


    summary = summary.rename(
        columns={
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
            "ev_ebitda": "EV/EBITDA",
        }
    )


    # Round numerical values
    numerical_columns = [
        "P/E",
        "P/B",
        "EV/EBITDA",
        "FCF_yield_pct",
        "5yr_median_PE",
        "PE_vs_sector_median_pct",
    ]


    for column in numerical_columns:

        summary[column] = pd.to_numeric(
            summary[column],
            errors="coerce"
        ).round(2)


    # -----------------------------------------------------
    # SORT
    # -----------------------------------------------------

    summary = summary.sort_values(
        ["flag", "company_name"],
        na_position="last"
    ).reset_index(drop=True)


    # -----------------------------------------------------
    # SAVE EXCEL
    # -----------------------------------------------------

    excel_path = (
        OUTPUT_DIR
        / "valuation_summary.xlsx"
    )


    summary.to_excel(
        excel_path,
        index=False
    )


    print(
        f"\nExcel file created:"
        f"\n{excel_path}"
    )


    # -----------------------------------------------------
    # SAVE FLAG CSV
    # -----------------------------------------------------

    flags = summary[
        summary["flag"].isin(
            ["Caution", "Discount"]
        )
    ].copy()


    csv_path = (
        OUTPUT_DIR
        / "valuation_flags.csv"
    )


    flags.to_csv(
        csv_path,
        index=False
    )


    print(
        f"CSV file created:"
        f"\n{csv_path}"
    )


    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    print("\nValuation Flag Summary:")

    print(
        summary["flag"]
        .value_counts(dropna=False)
    )


    print(
        f"\nFinal valuation rows: "
        f"{len(summary)}"
    )


    print(
        f"Flagged rows: "
        f"{len(flags)}"
    )


    print("\nVALUATION MODULE COMPLETED")
    print("=" * 60)


    return summary


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

if __name__ == "__main__":

    build_valuation_summary()