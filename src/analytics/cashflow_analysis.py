import sqlite3

from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_quality_score,
    calculate_capex_intensity,
    calculate_fcf_conversion_rate,
    classify_capital_allocation,
    detect_distress_signal,
    detect_deleveraging,
)


DB_PATH = "data/nifty100.db"


def get_sign(value):
    """Return + or - based on the value."""
    if value is None:
        return None

    if value >= 0:
        return "+"

    return "-"


def calculate_all_free_cash_flow(db_path=DB_PATH):
    """
    Calculate Free Cash Flow for every company-year.
    """

    conn = sqlite3.connect(db_path)

    rows = conn.execute(
        """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity
        FROM cashflow
        ORDER BY company_id, year
        """
    ).fetchall()

    conn.close()

    results = []

    for company_id, year, cfo, cfi in rows:
        fcf = calculate_free_cash_flow(cfo, cfi)

        results.append(
            {
                "company_id": company_id,
                "year": year,
                "free_cash_flow": fcf,
            }
        )

    return results


def calculate_all_cashflow_kpis(db_path=DB_PATH):
    """
    Calculate all available cash-flow KPIs
    for every company-year.

    Combines cashflow and profitandloss data.
    """

    conn = sqlite3.connect(db_path)

    rows = conn.execute(
        """
        SELECT
            c.company_id,
            c.year,
            c.operating_activity,
            c.investing_activity,
            c.financing_activity,
            p.sales,
            p.net_profit,
            p.operating_profit
        FROM cashflow c
        LEFT JOIN profitandloss p
            ON c.company_id = p.company_id
            AND c.year = p.year
        ORDER BY c.company_id, c.year
        """
    ).fetchall()

    conn.close()

    results = []

    for (
        company_id,
        year,
        cfo,
        cfi,
        cff,
        sales,
        pat,
        operating_profit,
    ) in rows:

        fcf = calculate_free_cash_flow(cfo, cfi)

        capex_intensity, capex_classification = calculate_capex_intensity(
            cfi,
            sales,
        )

        fcf_conversion = calculate_fcf_conversion_rate(
            fcf,
            operating_profit,
        )

        if cfo is not None and pat is not None and pat != 0:
            cfo_pat_ratio = cfo / pat
        else:
            cfo_pat_ratio = None

        capital_allocation = classify_capital_allocation(
            get_sign(cfo),
            get_sign(cfi),
            get_sign(cff),
            cfo_pat_ratio,
        )

        results.append(
            {
                "company_id": company_id,
                "year": year,
                "cfo": cfo,
                "cfi": cfi,
                "cff": cff,
                "sales": sales,
                "net_profit": pat,
                "operating_profit": operating_profit,
                "free_cash_flow": fcf,
                "capex_intensity": capex_intensity,
                "capex_classification": capex_classification,
                "fcf_conversion_rate": fcf_conversion,
                "cfo_pat_ratio": cfo_pat_ratio,
                "capital_allocation": capital_allocation,
            }
        )

    return results


def calculate_cfo_quality_by_company(db_path=DB_PATH):
    """
    Calculate the 5-year average CFO/PAT ratio
    for every company.

    Uses the latest 5 available company-years.
    """

    conn = sqlite3.connect(db_path)

    rows = conn.execute(
        """
        SELECT
            c.company_id,
            c.year,
            c.operating_activity,
            p.net_profit
        FROM cashflow c
        JOIN profitandloss p
            ON c.company_id = p.company_id
            AND c.year = p.year
        ORDER BY c.company_id, c.year
        """
    ).fetchall()

    conn.close()

    company_data = {}

    for company_id, year, cfo, pat in rows:
        company_data.setdefault(company_id, []).append(
            (year, cfo, pat)
        )

    results = []

    for company_id, records in company_data.items():

        latest_five = records[-5:]

        years = [record[0] for record in latest_five]
        cfo_values = [record[1] for record in latest_five]
        pat_values = [record[2] for record in latest_five]

        ratio, classification = calculate_cfo_quality_score(
            cfo_values,
            pat_values,
        )

        results.append(
            {
                "company_id": company_id,
                "years_used": years,
                "cfo_pat_ratio": ratio,
                "cfo_quality": classification,
            }
        )

    return results


def calculate_deleveraging_by_company(db_path=DB_PATH):
    """
    Detect deleveraging for each company.

    Condition:
        Latest CFF < 0
        AND latest borrowings < previous-year borrowings.
    """

    conn = sqlite3.connect(db_path)

    rows = conn.execute(
        """
        SELECT
            c.company_id,
            c.year,
            c.financing_activity,
            b.borrowings
        FROM cashflow c
        LEFT JOIN balancesheet b
            ON c.company_id = b.company_id
            AND c.year = b.year
        ORDER BY c.company_id, c.year
        """
    ).fetchall()

    conn.close()

    company_data = {}

    for company_id, year, cff, borrowings in rows:
        company_data.setdefault(company_id, []).append(
            (year, cff, borrowings)
        )

    results = []

    for company_id, records in company_data.items():

        if len(records) < 2:
            results.append(
                {
                    "company_id": company_id,
                    "deleveraging_flag": False,
                }
            )
            continue

        latest = records[-1]
        previous = records[-2]

        latest_year, latest_cff, latest_borrowings = latest
        previous_year, previous_cff, previous_borrowings = previous

        flag = detect_deleveraging(
            latest_cff,
            latest_borrowings,
            previous_borrowings,
        )

        results.append(
            {
                "company_id": company_id,
                "deleveraging_flag": flag,
            }
        )

    return results