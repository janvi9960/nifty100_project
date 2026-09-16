import os
import sqlite3

import pandas as pd

from src.analytics.cashflow_kpis import (
    calculate_cfo_quality_score,
    calculate_capex_intensity,
    calculate_fcf_conversion_rate,
    classify_capital_allocation,
    detect_distress_signal,
    detect_deleveraging,
)


DB_PATH = "data/nifty100.db"
OUTPUT_PATH = "output/cashflow_intelligence.xlsx"


def _unwrap_result(result):
    """
    Safely extract the main numeric value from KPI functions.

    Some existing KPI functions return:
        value

    while others return:
        (value, label)
    """

    if isinstance(result, tuple):
        if len(result) > 0:
            return result[0]

        return None

    return result


def _extract_label(result):
    """
    Extract a label when an existing KPI function returns:
        (value, label)
    """

    if isinstance(result, tuple):

        if len(result) > 1:
            return result[1]

    return None


def _safe_cagr(start_value, end_value, periods):
    """
    Calculate CAGR safely.

    CAGR is not meaningful when the starting FCF
    is zero or negative.
    """

    if (
        start_value is None
        or end_value is None
        or periods <= 0
        or start_value <= 0
        or end_value < 0
    ):
        return None

    return (
        (end_value / start_value) ** (1 / periods) - 1
    ) * 100


def _cfo_quality_label(score):
    """
    Classify CFO/PAT quality.

    > 1.0      -> High Quality
    0.5 - 1.0  -> Moderate
    < 0.5      -> Accrual Risk
    """

    if score is None:
        return None

    if score > 1.0:
        return "High Quality"

    if score >= 0.5:
        return "Moderate"

    return "Accrual Risk"


def _capex_label(capex_intensity):
    """
    Classify CapEx intensity.

    < 3%       -> Asset Light
    3% - 8%     -> Moderate
    > 8%         -> Capital Intensive
    """

    if capex_intensity is None:
        return None

    if capex_intensity < 3:
        return "Asset Light"

    if capex_intensity <= 8:
        return "Moderate"

    return "Capital Intensive"


def _get_sign(value):
    """
    Convert a cash-flow value into +, -, or 0.
    """

    if value is None:
        return None

    if value > 0:
        return "+"

    if value < 0:
        return "-"

    return "0"


def _get_cfo_pat_ratio(cfo, pat):
    """
    Calculate CFO/PAT ratio.
    """

    if cfo is None or pat in (None, 0):
        return None

    return cfo / pat


def _calculate_company_metrics(company_id, rows):
    """
    Calculate all latest-year cash-flow intelligence
    metrics for one company.
    """

    rows = sorted(
        rows,
        key=lambda x: x["year"],
    )

    latest = rows[-1]

    latest_year = latest["year"]

    # =========================================================
    # CFO QUALITY
    # =========================================================

    cfo_values = []
    pat_values = []

    for row in rows[-5:]:

        if (
            row["cfo"] is not None
            and row["pat"] is not None
        ):

            cfo_values.append(
                row["cfo"]
            )

            pat_values.append(
                row["pat"]
            )

    cfo_quality_result = (
        calculate_cfo_quality_score(
            cfo_values,
            pat_values,
        )
    )

    cfo_quality_score = _unwrap_result(
        cfo_quality_result
    )

    cfo_quality_label = _extract_label(
        cfo_quality_result
    )

    if cfo_quality_label is None:

        cfo_quality_label = (
            _cfo_quality_label(
                cfo_quality_score
            )
        )

    # =========================================================
    # LATEST YEAR VALUES
    # =========================================================

    latest_cfo = latest["cfo"]
    latest_cfi = latest["cfi"]
    latest_cff = latest["cff"]
    latest_sales = latest["sales"]
    latest_operating_profit = (
        latest["operating_profit"]
    )
    latest_pat = latest["pat"]

    # =========================================================
    # FREE CASH FLOW
    # =========================================================

    latest_fcf = None

    if (
        latest_cfo is not None
        and latest_cfi is not None
    ):

        latest_fcf = (
            latest_cfo + latest_cfi
        )

    # =========================================================
    # CAPEX INTENSITY
    # =========================================================

    capex_result = calculate_capex_intensity(
        latest_cfi,
        latest_sales,
    )

    capex_intensity_pct = _unwrap_result(
        capex_result
    )

    capex_label = _extract_label(
        capex_result
    )

    if capex_label is None:

        capex_label = _capex_label(
            capex_intensity_pct
        )

    # =========================================================
    # FCF CONVERSION
    # =========================================================

    fcf_conversion_result = (
        calculate_fcf_conversion_rate(
            latest_fcf,
            latest_operating_profit,
        )
    )

    fcf_conversion_pct = _unwrap_result(
        fcf_conversion_result
    )

    # =========================================================
    # FCF CAGR - 5 YEAR
    # =========================================================

    fcf_by_year = {}

    for row in rows:

        if (
            row["cfo"] is None
            or row["cfi"] is None
        ):
            continue

        fcf_by_year[row["year"]] = (
            row["cfo"] + row["cfi"]
        )

    fcf_cagr_5yr = None

    target_start_year = (
        latest_year - 5
    )

    if (
        target_start_year in fcf_by_year
        and latest_year in fcf_by_year
    ):

        fcf_cagr_5yr = _safe_cagr(
            fcf_by_year[
                target_start_year
            ],
            fcf_by_year[
                latest_year
            ],
            5,
        )

    # =========================================================
    # DISTRESS SIGNAL
    # =========================================================

    distress_flag = (
        detect_distress_signal(
            latest_cfo,
            latest_cff,
        )
    )

    # =========================================================
    # DELEVERAGING
    # =========================================================

    borrowings_history = [
        row
        for row in rows
        if row["borrowings"] is not None
    ]

    deleveraging_flag = False

    if len(borrowings_history) >= 2:

        latest_borrowings = (
            borrowings_history[-1][
                "borrowings"
            ]
        )

        previous_borrowings = (
            borrowings_history[-2][
                "borrowings"
            ]
        )

        deleveraging_flag = (
            detect_deleveraging(
                latest_cff,
                latest_borrowings,
                previous_borrowings,
            )
        )

    # =========================================================
    # CAPITAL ALLOCATION
    # =========================================================

    cfo_sign = _get_sign(
        latest_cfo
    )

    cfi_sign = _get_sign(
        latest_cfi
    )

    cff_sign = _get_sign(
        latest_cff
    )

    cfo_pat_ratio = (
        _get_cfo_pat_ratio(
            latest_cfo,
            latest_pat,
        )
    )

    capital_allocation_label = (
        classify_capital_allocation(
            cfo_sign,
            cfi_sign,
            cff_sign,
            cfo_pat_ratio,
        )
    )

    # =========================================================
    # FINAL RESULT
    # =========================================================

    return {
        "company_id": company_id,
        "sector": latest["sector"],
        "cfo_quality_score": (
            cfo_quality_score
        ),
        "cfo_quality_label": (
            cfo_quality_label
        ),
        "capex_intensity_pct": (
            capex_intensity_pct
        ),
        "capex_label": capex_label,
        "fcf_cagr_5yr": fcf_cagr_5yr,
        "fcf_conversion_pct": (
            fcf_conversion_pct
        ),
        "distress_flag": distress_flag,
        "deleveraging_flag": (
            deleveraging_flag
        ),
        "capital_allocation_label": (
            capital_allocation_label
        ),
    }


def build_cashflow_intelligence(
    db_path=DB_PATH,
    output_path=OUTPUT_PATH,
):
    """
    Build the final Cash Flow Intelligence Excel report.
    """

    # =========================================================
    # DATABASE CONNECTION
    # =========================================================

    conn = sqlite3.connect(
        db_path
    )

    query = """
        SELECT
            c.company_id,
            c.year,
            c.operating_activity AS cfo,
            c.investing_activity AS cfi,
            c.financing_activity AS cff,
            b.borrowings,
            p.sales,
            p.operating_profit,
            p.net_profit AS pat,
            s.broad_sector AS sector

        FROM cashflow c

        LEFT JOIN balancesheet b
            ON c.company_id = b.company_id
            AND c.year = b.year

        LEFT JOIN profitandloss p
            ON c.company_id = p.company_id
            AND c.year = p.year

        LEFT JOIN sectors s
            ON c.company_id = s.company_id

        ORDER BY
            c.company_id,
            c.year
    """

    df = pd.read_sql_query(
        query,
        conn,
    )

    conn.close()

    # =========================================================
    # COMPANY-WISE CALCULATIONS
    # =========================================================

    results = []

    for company_id, group in df.groupby(
        "company_id",
        sort=True,
    ):

        rows = []

        for _, row in group.iterrows():

            rows.append(
                {
                    "year": int(
                        row["year"]
                    ),
                    "cfo": row["cfo"],
                    "cfi": row["cfi"],
                    "cff": row["cff"],
                    "borrowings": (
                        row["borrowings"]
                    ),
                    "sales": row["sales"],
                    "operating_profit": (
                        row[
                            "operating_profit"
                        ]
                    ),
                    "pat": row["pat"],
                    "sector": row["sector"],
                }
            )

        company_result = (
            _calculate_company_metrics(
                company_id,
                rows,
            )
        )

        results.append(
            company_result
        )

    result_df = pd.DataFrame(
        results
    )

    # =========================================================
    # REQUIRED COLUMN ORDER
    # =========================================================

    columns = [
        "company_id",
        "sector",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag",
        "capital_allocation_label",
    ]

    result_df = result_df[
        columns
    ]

    # =========================================================
    # CREATE OUTPUT DIRECTORY
    # =========================================================

    output_directory = os.path.dirname(
        output_path
    )

    if output_directory:

        os.makedirs(
            output_directory,
            exist_ok=True,
        )

    # =========================================================
    # WRITE EXCEL
    # =========================================================

    with pd.ExcelWriter(
        output_path,
        engine="openpyxl",
    ) as writer:

        result_df.to_excel(
            writer,
            sheet_name="Cash Flow Intelligence",
            index=False,
        )

    # =========================================================
    # FINAL REPORT
    # =========================================================

    print(
        "CASH FLOW INTELLIGENCE REPORT COMPLETED"
    )

    print(
        "Companies written:",
        len(result_df),
    )

    print(
        "Columns:",
        len(result_df.columns),
    )

    print(
        "Output:",
        output_path,
    )

    print(
        "\nCapital Allocation Distribution:"
    )

    print(
        result_df[
            "capital_allocation_label"
        ].value_counts(
            dropna=False
        )
    )

    print(
        "\nDistress flags:"
    )

    print(
        result_df[
            "distress_flag"
        ].sum()
    )

    print(
        "\nDeleveraging flags:"
    )

    print(
        result_df[
            "deleveraging_flag"
        ].sum()
    )

    return result_df