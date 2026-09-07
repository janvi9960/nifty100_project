
import sqlite3
from pathlib import Path
import pandas as pd


DB_PATH = Path("data/nifty100.db")
COMPANIES_PATH = Path("data/companies.xlsx")
OUTPUT_PATH = Path("output/ratio_edge_cases.log")


def classify_anomaly(engine_value, source_value, difference):
    """
    Categorize a ROE/ROCE anomaly.

    This is a practical classification for Sprint 2 documentation.
    """

    if pd.isna(source_value):
        return "DATA SOURCE ISSUE"

    if engine_value is None:
        return "DATA SOURCE ISSUE"

    # Large difference usually indicates a formula/version/source mismatch.
    if difference > 20:
        return "FORMULA DISCREPANCY"

    return "VERSION DIFFERENCE"


def main():
    print("=" * 60)
    print("RATIO EDGE CASE CHECKER")
    print("=" * 60)

    # ---------------------------------------------------------
    # Validate files
    # ---------------------------------------------------------

    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    if not COMPANIES_PATH.exists():
        raise FileNotFoundError(f"Companies file not found: {COMPANIES_PATH}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # Load source company data
    # ---------------------------------------------------------

    companies = pd.read_excel(
        COMPANIES_PATH,
        header=1
    )

    companies["id"] = companies["id"].astype(str).str.strip()

    # ---------------------------------------------------------
    # Load calculated ROE / ROCE from SQLite
    # ---------------------------------------------------------

    conn = sqlite3.connect(DB_PATH)

    ratios = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            return_on_equity,
            return_on_capital
        FROM financial_ratios
        ORDER BY company_id, year
        """,
        conn
    )

    conn.close()

    ratios["company_id"] = ratios["company_id"].astype(str).str.strip()

    # ---------------------------------------------------------
    # Generate anomaly log
    # ---------------------------------------------------------

    log_lines = []

    log_lines.append("=" * 80)
    log_lines.append("FINANCIAL RATIO EDGE CASE LOG")
    log_lines.append("=" * 80)
    log_lines.append("")
    log_lines.append(
        "ROE/ROCE engine values are compared with the source values "
        "provided in companies.xlsx."
    )
    log_lines.append(
        "Because companies.xlsx contains one source value per company, "
        "the comparison is treated as a source cross-check rather than "
        "a historical year-by-year validation."
    )
    log_lines.append("")

    anomaly_count = 0

    # ---------------------------------------------------------
    # Compare company-level source values
    # ---------------------------------------------------------

    for _, company in companies.iterrows():

        company_id = company["id"]
        company_name = str(company.get("company_name", "")).strip()

        source_roe = company.get("roe_percentage")
        source_roce = company.get("roce_percentage")

        company_ratios = ratios[
            ratios["company_id"] == company_id
        ]

        if company_ratios.empty:
            log_lines.append(
                f"[DATA SOURCE ISSUE] {company_id} - "
                f"{company_name}: No calculated ratio rows found."
            )
            anomaly_count += 1
            continue

        # -----------------------------------------------------
        # ROE comparison
        # -----------------------------------------------------

        roe_values = company_ratios["return_on_equity"].dropna()

        if pd.isna(source_roe):
            log_lines.append(
                f"[DATA SOURCE ISSUE] {company_id} - {company_name}: "
                f"Source ROE is missing."
            )
            anomaly_count += 1

        elif not roe_values.empty:

            # Compare source value against the latest available
            # calculated value.
            latest_roe = roe_values.iloc[-1]

            difference = abs(float(latest_roe) - float(source_roe))

            if difference > 5:
                category = classify_anomaly(
                    latest_roe,
                    source_roe,
                    difference
                )

                log_lines.append(
                    f"[{category}] {company_id} - {company_name} | "
                    f"ROE | "
                    f"Engine={latest_roe:.2f}% | "
                    f"Source={float(source_roe):.2f}% | "
                    f"Difference={difference:.2f}%"
                )

                anomaly_count += 1

        # -----------------------------------------------------
        # ROCE comparison
        # -----------------------------------------------------

        roce_values = company_ratios["return_on_capital"].dropna()

        if pd.isna(source_roce):
            log_lines.append(
                f"[DATA SOURCE ISSUE] {company_id} - {company_name}: "
                f"Source ROCE is missing."
            )
            anomaly_count += 1

        elif not roce_values.empty:

            latest_roce = roce_values.iloc[-1]

            difference = abs(float(latest_roce) - float(source_roce))

            if difference > 5:
                category = classify_anomaly(
                    latest_roce,
                    source_roce,
                    difference
                )

                log_lines.append(
                    f"[{category}] {company_id} - {company_name} | "
                    f"ROCE | "
                    f"Engine={latest_roce:.2f}% | "
                    f"Source={float(source_roce):.2f}% | "
                    f"Difference={difference:.2f}%"
                )

                anomaly_count += 1

    # ---------------------------------------------------------
    # Check Financials-sector leverage suppression
    # ---------------------------------------------------------

    log_lines.append("")
    log_lines.append("=" * 80)
    log_lines.append("FINANCIALS SECTOR LEVERAGE CHECK")
    log_lines.append("=" * 80)

    conn = sqlite3.connect(DB_PATH)

    try:
        sector_rows = pd.read_sql_query(
            """
            SELECT
                company_id,
                broad_sector
            FROM sectors
            """,
            conn
        )
    except Exception:
        sector_rows = pd.DataFrame(
            columns=["company_id", "broad_sector"]
        )

    conn.close()

    financial_companies = set(
        sector_rows.loc[
            sector_rows["broad_sector"].astype(str).str.lower()
            == "financials",
            "company_id"
        ].astype(str)
    )

    if financial_companies:

        conn = sqlite3.connect(DB_PATH)

        leverage = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                debt_to_equity,
                high_leverage_flag
            FROM financial_ratios
            """,
            conn
        )

        conn.close()

        leverage["company_id"] = leverage["company_id"].astype(str)

        financial_rows = leverage[
            leverage["company_id"].isin(financial_companies)
        ]

        incorrect_flags = financial_rows[
            financial_rows["high_leverage_flag"] == 1
        ]

        if incorrect_flags.empty:
            log_lines.append(
                "PASS: Financials-sector high leverage warnings "
                "are suppressed."
            )
        else:
            log_lines.append(
                f"[FORMULA DISCREPANCY] {len(incorrect_flags)} "
                f"Financials-sector rows have high_leverage_flag=1."
            )

    else:
        log_lines.append(
            "DATA SOURCE ISSUE: No Financials-sector companies "
            "were found in the sectors table."
        )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    log_lines.append("")
    log_lines.append("=" * 80)
    log_lines.append("SUMMARY")
    log_lines.append("=" * 80)
    log_lines.append(
        f"Companies checked: {len(companies)}"
    )
    log_lines.append(
        f"Ratio rows checked: {len(ratios)}"
    )
    log_lines.append(
        f"Anomalies documented: {anomaly_count}"
    )
    log_lines.append("")
    log_lines.append(
        "Categories used:"
    )
    log_lines.append(
        "DATA SOURCE ISSUE = missing or unavailable source/calculated data"
    )
    log_lines.append(
        "VERSION DIFFERENCE = source and engine values differ but may "
        "reflect different source versions"
    )
    log_lines.append(
        "FORMULA DISCREPANCY = unusually large difference requiring "
        "formula/data investigation"
    )
    log_lines.append("")
    log_lines.append("=" * 80)

    # ---------------------------------------------------------
    # Write log
    # ---------------------------------------------------------

    OUTPUT_PATH.write_text(
        "\n".join(log_lines),
        encoding="utf-8"
    )

    print()
    print("=" * 60)
    print("EDGE CASE CHECK COMPLETED")
    print("=" * 60)
    print(f"Companies checked: {len(companies)}")
    print(f"Ratio rows checked: {len(ratios)}")
    print(f"Anomalies documented: {anomaly_count}")
    print(f"Output file: {OUTPUT_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()

