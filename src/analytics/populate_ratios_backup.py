import sqlite3
from pathlib import Path

from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roe,
    calculate_roce,
    calculate_roa,
    calculate_debt_to_equity,
    check_high_leverage,
    calculate_asset_turnover,
)

from src.analytics.cagr import calculate_cagr

from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_capex_intensity,
    calculate_fcf_conversion_rate,
)


DB_PATH = Path("data/nifty100.db")


def get_connection():
    """Create SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def load_source_data(conn):
    """
    Load P&L, balance sheet, cash flow and sector data.
    """

    # =========================================================
    # P&L
    # =========================================================

    pnl = {}

    rows = conn.execute(
        """
        SELECT
            company_id,
            year,
            sales,
            operating_profit,
            net_profit,
            eps,
            opm_percentage,
            dividend_payout_ratio_pct,
            other_income,
            interest
        FROM profitandloss
        ORDER BY company_id, year
        """
    ).fetchall()

    for row in rows:
        (
            company_id,
            year,
            sales,
            operating_profit,
            net_profit,
            eps,
            opm_percentage,
            dividend_payout_ratio_pct,
            other_income,
            interest,
        ) = row

        pnl[(company_id, year)] = {
            "sales": sales,
            "operating_profit": operating_profit,
            "net_profit": net_profit,
            "eps": eps,
            "opm_percentage": opm_percentage,
            "dividend_payout_ratio_pct": dividend_payout_ratio_pct,
            "other_income": other_income,
            "interest": interest,
        }

    # =========================================================
    # BALANCE SHEET
    # =========================================================

    balance_sheet = {}

    rows = conn.execute(
        """
        SELECT
            company_id,
            year,
            borrowings,
            total_assets,
            equity,
            reserves
        FROM balancesheet
        """
    ).fetchall()

    for row in rows:
        (
            company_id,
            year,
            borrowings,
            total_assets,
            equity,
            reserves,
        ) = row

        balance_sheet[(company_id, year)] = {
            "borrowings": borrowings,
            "total_assets": total_assets,
            "equity": equity,
            "reserves": reserves,
        }

    # =========================================================
    # CASH FLOW
    # =========================================================

    cashflow = {}

    rows = conn.execute(
        """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity
        FROM cashflow
        """
    ).fetchall()

    for row in rows:
        (
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity,
        ) = row

        cashflow[(company_id, year)] = {
            "cfo": operating_activity,
            "cfi": investing_activity,
            "cff": financing_activity,
        }

    # =========================================================
    # SECTORS
    # =========================================================

    sectors = {}

    rows = conn.execute(
        """
        SELECT
            company_id,
            broad_sector,
            sub_sector
        FROM sectors
        """
    ).fetchall()

    for company_id, broad_sector, sub_sector in rows:
        sectors[company_id] = {
            "broad_sector": broad_sector,
            "sub_sector": sub_sector,
        }

    print("=" * 60)
    print("LOADING SOURCE DATA")
    print("=" * 60)
    print(f"P&L company-years: {len(pnl)}")
    print(f"Balance Sheet company-years: {len(balance_sheet)}")
    print(f"Cash Flow company-years: {len(cashflow)}")
    print(f"Companies with sector data: {len(sectors)}")

    return pnl, balance_sheet, cashflow, sectors


def calculate_5yr_cagr(pnl, company_id, year, field):
    """
    Calculate 5-year CAGR using year and year-5.
    """

    start_key = (company_id, year - 5)
    end_key = (company_id, year)

    if start_key not in pnl or end_key not in pnl:
        return None, "INSUFFICIENT"

    start_value = pnl[start_key].get(field)
    end_value = pnl[end_key].get(field)

    if start_value is None or end_value is None:
        return None, "INSUFFICIENT"

    return calculate_cagr(
        start_value,
        end_value,
        5,
    )


def calculate_row(
    company_id,
    year,
    pnl,
    balance_sheet,
    cashflow,
    sectors,
):
    """Calculate all supported KPIs for one company-year."""

    p = pnl[(company_id, year)]

    bs = balance_sheet.get((company_id, year))
    cf = cashflow.get((company_id, year))

    sales = p.get("sales")
    operating_profit = p.get("operating_profit")
    net_profit = p.get("net_profit")

    eps = p.get("eps")
    dividend_payout = p.get("dividend_payout_ratio_pct")

    other_income = p.get("other_income")
    interest = p.get("interest")

    # =========================================================
    # BALANCE SHEET VALUES
    # =========================================================

    if bs:
        borrowings = bs.get("borrowings")
        total_assets = bs.get("total_assets")
        equity = bs.get("equity")
        reserves = bs.get("reserves")
    else:
        borrowings = None
        total_assets = None
        equity = None
        reserves = None

    # =========================================================
    # PROFITABILITY RATIOS
    # =========================================================

    npm = None
    opm = None
    roe = None
    roce = None
    roa = None

    if sales is not None and net_profit is not None:
        npm = calculate_net_profit_margin(
            net_profit,
            sales,
        )

    if sales is not None and operating_profit is not None:
        opm = calculate_operating_profit_margin(
            operating_profit,
            sales,
        )

    if (
        bs
        and net_profit is not None
        and equity is not None
        and reserves is not None
    ):
        roe = calculate_roe(
            net_profit,
            equity,
            reserves,
        )

    if (
        bs
        and operating_profit is not None
        and equity is not None
        and reserves is not None
        and borrowings is not None
    ):
        roce = calculate_roce(
            operating_profit,
            equity,
            reserves,
            borrowings,
        )

    if (
        bs
        and net_profit is not None
        and total_assets is not None
    ):
        roa = calculate_roa(
            net_profit,
            total_assets,
        )

    # =========================================================
    # LEVERAGE
    # =========================================================

    debt_to_equity = None
    high_leverage_flag = False

    if (
        bs
        and borrowings is not None
        and equity is not None
        and reserves is not None
    ):
        debt_to_equity = calculate_debt_to_equity(
            borrowings,
            equity,
            reserves,
        )

        sector = sectors.get(company_id, {})
        broad_sector = sector.get("broad_sector")

        high_leverage_flag = check_high_leverage(
            debt_to_equity,
            broad_sector,
        )

    # =========================================================
    # ASSET TURNOVER
    # =========================================================

    asset_turnover = None

    if (
        bs
        and sales is not None
        and total_assets is not None
    ):
        asset_turnover = calculate_asset_turnover(
            sales,
            total_assets,
        )

    # =========================================================
    # CASH FLOW KPIs
    # =========================================================

    free_cash_flow = None
    capex = None
    cash_from_operations = None
    fcf_conversion_rate = None

    if cf:
        cfo = cf.get("cfo")
        cfi = cf.get("cfi")

        if cfo is not None and cfi is not None:

            free_cash_flow = calculate_free_cash_flow(
                cfo,
                cfi,
            )

            cash_from_operations = cfo

            # Store CapEx as positive magnitude.
            capex = abs(cfi)

            if sales is not None:
                capex_intensity, _ = calculate_capex_intensity(
                    cfi,
                    sales,
                )
            else:
                capex_intensity = None

            if operating_profit is not None:
                fcf_conversion_rate = (
                    calculate_fcf_conversion_rate(
                        free_cash_flow,
                        operating_profit,
                    )
                )

    # =========================================================
    # INTEREST COVERAGE RATIO
    # =========================================================

    interest_coverage = None
    icr_label = None
    icr_warning_flag = False

    if interest is not None:

        if interest == 0:

            icr_label = "Debt Free"

        elif operating_profit is not None:

            other_income_value = (
                other_income
                if other_income is not None
                else 0
            )

            interest_coverage = (
                operating_profit + other_income_value
            ) / interest

            icr_warning_flag = (
                interest_coverage < 1.5
            )

    # =========================================================
    # CAGR
    # =========================================================

    revenue_cagr, revenue_flag = calculate_5yr_cagr(
        pnl,
        company_id,
        year,
        "sales",
    )

    pat_cagr, pat_flag = calculate_5yr_cagr(
        pnl,
        company_id,
        year,
        "net_profit",
    )

    eps_cagr, eps_flag = calculate_5yr_cagr(
        pnl,
        company_id,
        year,
        "eps",
    )

    # =========================================================
    # OTHER FIELDS
    # =========================================================

    # Book value per share cannot be calculated because
    # shares outstanding are not available.

    book_value_per_share = None

    # Borrowings are the available debt measure.
    total_debt = borrowings

    # Composite score is left NULL because no official
    # scoring formula has been defined yet.

    composite_quality_score = None

    # =========================================================
    # RETURN RESULT
    # =========================================================

    return {
        "company_id": company_id,
        "year": year,

        "net_profit_margin": npm,
        "operating_profit_margin": opm,
        "return_on_equity": roe,
        "return_on_capital": roce,
        "return_on_assets": roa,

        "debt_to_equity": debt_to_equity,
        "high_leverage_flag": int(high_leverage_flag),

        "interest_coverage": interest_coverage,
        "icr_warning_flag": int(icr_warning_flag),
        "icr_label": icr_label,

        "asset_turnover": asset_turnover,

        "free_cash_flow": free_cash_flow,

        "earnings_per_share": eps,
        "book_value_per_share": book_value_per_share,
        "dividend_payout_ratio_pct": dividend_payout,

        "total_debt_cr": total_debt,
        "cash_from_operations_cr": cash_from_operations,
        "capex_cr": capex,

        "revenue_cagr": revenue_cagr,
        "pat_cagr": pat_cagr,
        "eps_cagr": eps_cagr,

        "revenue_cagr_5yr": revenue_cagr,
        "pat_cagr_5yr": pat_cagr,
        "eps_cagr_5yr": eps_cagr,

        "composite_quality_score": composite_quality_score,
    }


def populate_financial_ratios():
    """Populate the financial_ratios table."""

    conn = get_connection()

    try:

        pnl, balance_sheet, cashflow, sectors = (
            load_source_data(conn)
        )

        rows = []

        for company_id, year in pnl.keys():

            result = calculate_row(
                company_id,
                year,
                pnl,
                balance_sheet,
                cashflow,
                sectors,
            )

            rows.append(result)

        print(f"Rows calculated: {len(rows)}")
        print()

        # =====================================================
        # CLEAR OLD RESULTS
        # =====================================================

        conn.execute(
            "DELETE FROM financial_ratios"
        )

        # =====================================================
        # INSERT NEW RESULTS
        # =====================================================

        insert_sql = """
        INSERT INTO financial_ratios (
            company_id,
            year,

            net_profit_margin,
            operating_profit_margin,
            return_on_equity,
            return_on_capital,
            debt_to_equity,
            interest_coverage,
            free_cash_flow,

            revenue_cagr,
            pat_cagr,
            eps_cagr,

            asset_turnover,

            earnings_per_share,
            book_value_per_share,
            dividend_payout_ratio_pct,

            total_debt_cr,
            cash_from_operations_cr,
            capex_cr,

            revenue_cagr_5yr,
            pat_cagr_5yr,
            eps_cagr_5yr,

            composite_quality_score,
            return_on_assets,

            high_leverage_flag,
            icr_warning_flag,
            icr_label
        )
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?, ?,
            ?, ?,
            ?, ?, ?
        )
        """

        values = []

        for r in rows:

            values.append(
                (
                    r["company_id"],
                    r["year"],

                    r["net_profit_margin"],
                    r["operating_profit_margin"],
                    r["return_on_equity"],
                    r["return_on_capital"],
                    r["debt_to_equity"],
                    r["interest_coverage"],
                    r["free_cash_flow"],

                    r["revenue_cagr"],
                    r["pat_cagr"],
                    r["eps_cagr"],

                    r["asset_turnover"],

                    r["earnings_per_share"],
                    r["book_value_per_share"],
                    r["dividend_payout_ratio_pct"],

                    r["total_debt_cr"],
                    r["cash_from_operations_cr"],
                    r["capex_cr"],

                    r["revenue_cagr_5yr"],
                    r["pat_cagr_5yr"],
                    r["eps_cagr_5yr"],

                    r["composite_quality_score"],
                    r["return_on_assets"],

                    r["high_leverage_flag"],
                    r["icr_warning_flag"],
                    r["icr_label"],
                )
            )

        conn.executemany(
            insert_sql,
            values,
        )

        conn.commit()

        # =====================================================
        # VALIDATION
        # =====================================================

        count = conn.execute(
            "SELECT COUNT(*) FROM financial_ratios"
        ).fetchone()[0]

        companies = conn.execute(
            """
            SELECT COUNT(DISTINCT company_id)
            FROM financial_ratios
            """
        ).fetchone()[0]

        year_range = conn.execute(
            """
            SELECT MIN(year), MAX(year)
            FROM financial_ratios
            """
        ).fetchone()

        print("=" * 60)
        print("FINANCIAL RATIO ENGINE COMPLETED")
        print("=" * 60)
        print(f"Rows inserted: {count}")
        print(f"Companies covered: {companies}")
        print(
            f"Year range: {year_range[0]} - {year_range[1]}"
        )
        print("=" * 60)

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


if __name__ == "__main__":
    populate_financial_ratios()

