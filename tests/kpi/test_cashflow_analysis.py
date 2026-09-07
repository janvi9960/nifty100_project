import sqlite3

from src.analytics.cashflow_analysis import (
    calculate_all_free_cash_flow,
    calculate_all_cashflow_kpis,
    calculate_cfo_quality_by_company,
)


DB_PATH = "data/nifty100.db"


def test_free_cash_flow_integration():
    data = calculate_all_free_cash_flow()

    assert len(data) == 1056

    abb_2012 = next(
        row
        for row in data
        if row["company_id"] == "ABB"
        and row["year"] == 2012
    )

    assert abb_2012["free_cash_flow"] == 42.0


def test_cashflow_kpis_integration():
    data = calculate_all_cashflow_kpis()

    assert len(data) == 1056

    abb_2012 = next(
        row
        for row in data
        if row["company_id"] == "ABB"
        and row["year"] == 2012
    )

    assert abb_2012["cfo"] == 101.0
    assert abb_2012["cfi"] == -59.0
    assert abb_2012["cff"] == -42.0
    assert abb_2012["free_cash_flow"] == 42.0

    assert round(
        abb_2012["capex_intensity"], 2
    ) == 3.57

    assert round(
        abb_2012["fcf_conversion_rate"], 2
    ) == 20.79

    assert round(
        abb_2012["cfo_pat_ratio"], 3
    ) == 0.697

    assert abb_2012["capital_allocation"] == "Reinvestor"


def test_cfo_quality_company_integration():
    data = calculate_cfo_quality_by_company()

    assert len(data) == 91

    abb = next(
        row
        for row in data
        if row["company_id"] == "ABB"
    )

    assert abb["years_used"] == [
        2020,
        2021,
        2022,
        2023,
        2024,
    ]

    assert round(
        abb["cfo_pat_ratio"], 3
    ) == 1.049

    assert abb["cfo_quality"] == "High Quality"


def test_cashflow_company_coverage():
    conn = sqlite3.connect(DB_PATH)

    cashflow_companies = conn.execute(
        """
        SELECT COUNT(DISTINCT company_id)
        FROM cashflow
        """
    ).fetchone()[0]

    matched_companies = conn.execute(
        """
        SELECT COUNT(DISTINCT c.company_id)
        FROM cashflow c
        JOIN profitandloss p
            ON c.company_id = p.company_id
            AND c.year = p.year
        """
    ).fetchone()[0]

    conn.close()

    assert cashflow_companies == 91
    assert matched_companies == 91
    assert cashflow_companies == matched_companies