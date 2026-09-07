import sqlite3
from pathlib import Path

import pandas as pd

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
COMPANIES_FILE = Path("data/companies.xlsx")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """Create SQLite connection."""

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


# ============================================================
# COMPANY DATA
# ============================================================

def load_company_data():
    """
    Load company-level data from companies.xlsx.

    Book value is stored at company level in the source file.
    It is used as Book Value Per Share.
    """

    df = pd.read_excel(
        COMPANIES_FILE,
        header=1,
    )

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
    )

    companies = {}

    for _, row in df.iterrows():

        company_id = row.get("id")

        if pd.isna(company_id):
            continue

        company_id = str(company_id).strip().upper()

        book_value = pd.to_numeric(
            row.get("book_value"),
            errors="coerce",
        )

        if pd.isna(book_value):
            book_value = None

        companies[company_id] = {
            "book_value": book_value,
        }

    print(f"Company master records: {len(companies)}")

    return companies


# ============================================================
# SOURCE DATA LOADING
# ============================================================

def load_source_data(conn):
    """
    Load P&L, balance sheet, cash flow and sector data.

    P&L is the base table because it contains all
    available company-year records.
    """

    print("=" * 60)
    print("LOADING SOURCE DATA")
    print("=" * 60)

    # --------------------------------------------------------
    # Profit & Loss
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Balance Sheet
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Cash Flow
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Sector
    # --------------------------------------------------------

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

    print(f"P&L company-years: {len(pnl)}")
    print(f"Balance Sheet company-years: {len(balance_sheet)}")
    print(f"Cash Flow company-years: {len(cashflow)}")
    print(f"Companies with sector data: {len(sectors)}")

    return pnl, balance_sheet, cashflow, sectors


# ============================================================
# CAGR
# ============================================================

def calculate_window_cagr(
    pnl,
    company_id,
    year,
    field,
    window,
):
    """
    Calculate CAGR using year and year-window.

    Returns:
        (value, flag)
    """

    start_key = (
        company_id,
        year - window,
    )

    end_key = (
        company_id,
        year,
    )

    if start_key not in pnl or end_key not in pnl:
        return None, "INSUFFICIENT"

    start_value = pnl[start_key].get(field)
    end_value = pnl[end_key].get(field)

    if start_value is None or end_value is None:
        return None, "INSUFFICIENT"

    return calculate_cagr(
        start_value,
        end_value,
        window,
    )


def calculate_all_cagrs(
    pnl,
    company_id,
    year,
):
    """
    Calculate 3-year, 5-year and 10-year CAGR
    for Revenue, PAT and EPS.
    """

    result = {}

    fields = {
        "revenue": "sales",
        "pat": "net_profit",
        "eps": "eps",
    }

    windows = [3, 5, 10]

    for metric, field in fields.items():

        for window in windows:

            value, flag = calculate_window_cagr(
                pnl,
                company_id,
                year,
                field,
                window,
            )

            result[
                f"{metric}_cagr_{window}yr"
            ] = value

            result[
                f"{metric}_cagr_{window}yr_flag"
            ] = flag

    return result


# ============================================================
# ONE COMPANY-YEAR CALCULATION
# ============================================================

def calculate_row(
    company_id,
    year,
    pnl,
    balance_sheet,
    cashflow,
    sectors,
    companies,
):
    """
    Calculate all supported KPIs for one company-year.
    """

    p = pnl[
        (company_id, year)
    ]

    bs = balance_sheet.get(
        (company_id, year)
    )

    cf = cashflow.get(
        (company_id, year)
    )

    # --------------------------------------------------------
    # P&L values
    # --------------------------------------------------------

    sales = p.get("sales")

    operating_profit = p.get(
        "operating_profit"
    )

    net_profit = p.get(
        "net_profit"
    )

    eps = p.get("eps")

    dividend_payout = p.get(
        "dividend_payout_ratio_pct"
    )

    other_income = p.get(
        "other_income"
    )

    interest = p.get(
        "interest"
    )

    # --------------------------------------------------------
    # Balance Sheet values
    # --------------------------------------------------------

    if bs:

        borrowings = bs.get(
            "borrowings"
        )

        total_assets = bs.get(
            "total_assets"
        )

        equity = bs.get(
            "equity"
        )

        reserves = bs.get(
            "reserves"
        )

    else:

        borrowings = None
        total_assets = None
        equity = None
        reserves = None

    # ========================================================
    # PROFITABILITY RATIOS
    # ========================================================

    npm = None
    opm = None
    roe = None
    roce = None
    roa = None

    # --------------------------------------------------------
    # Net Profit Margin
    # --------------------------------------------------------

    if (
        sales is not None
        and net_profit is not None
    ):

        npm = calculate_net_profit_margin(
            net_profit,
            sales,
        )

    # --------------------------------------------------------
    # Operating Profit Margin
    # --------------------------------------------------------

    if (
        sales is not None
        and operating_profit is not None
    ):

        opm = calculate_operating_profit_margin(
            operating_profit,
            sales,
        )

    # --------------------------------------------------------
    # ROE
    # --------------------------------------------------------

    if (
        net_profit is not None
        and equity is not None
        and reserves is not None
    ):

        roe = calculate_roe(
            net_profit,
            equity,
            reserves,
        )

    # --------------------------------------------------------
    # ROCE
    # --------------------------------------------------------

    if (
        operating_profit is not None
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

    # --------------------------------------------------------
    # ROA
    # --------------------------------------------------------

    if (
        net_profit is not None
        and total_assets is not None
    ):

        roa = calculate_roa(
            net_profit,
            total_assets,
        )

    # ========================================================
    # LEVERAGE
    # ========================================================

    debt_to_equity = None
    high_leverage_flag = False

    if bs:

        debt_to_equity = calculate_debt_to_equity(
            borrowings,
            equity,
            reserves,
        )

        sector = sectors.get(
            company_id,
            {},
        )

        broad_sector = sector.get(
            "broad_sector"
        )

        high_leverage_flag = check_high_leverage(
            debt_to_equity,
            broad_sector,
        )

    # ========================================================
    # INTEREST COVERAGE RATIO
    # ========================================================

    interest_coverage = None
    icr_label = None
    icr_warning_flag = False

    if interest is not None:

        if interest == 0:

            interest_coverage = None
            icr_label = "Debt Free"
            icr_warning_flag = False

        elif (
            operating_profit is not None
        ):

            other_income_value = (
                other_income
                if other_income is not None
                else 0
            )

            interest_coverage = (
                operating_profit
                + other_income_value
            ) / interest

            icr_warning_flag = (
                interest_coverage < 1.5
            )

    # ========================================================
    # ASSET TURNOVER
    # ========================================================

    asset_turnover = None

    if (
        sales is not None
        and total_assets is not None
    ):

        asset_turnover = calculate_asset_turnover(
            sales,
            total_assets,
        )

    # ========================================================
    # CASH FLOW KPIs
    # ========================================================

    free_cash_flow = None
    capex = None
    cash_from_operations = None
    capex_intensity = None
    fcf_conversion_rate = None

    if cf:

        cfo = cf.get("cfo")
        cfi = cf.get("cfi")

        # ----------------------------------------------------
        # Free Cash Flow
        # ----------------------------------------------------

        free_cash_flow = calculate_free_cash_flow(
            cfo,
            cfi,
        )

        # ----------------------------------------------------
        # CFO
        # ----------------------------------------------------

        cash_from_operations = cfo

        # ----------------------------------------------------
        # CapEx
        # ----------------------------------------------------

        if cfi is not None:

            capex = abs(cfi)

        # ----------------------------------------------------
        # CapEx Intensity
        # ----------------------------------------------------

        if (
            cfi is not None
            and sales is not None
        ):

            capex_intensity, _ = (
                calculate_capex_intensity(
                    cfi,
                    sales,
                )
            )

        # ----------------------------------------------------
        # FCF Conversion Rate
        # ----------------------------------------------------

        fcf_conversion_rate = (
            calculate_fcf_conversion_rate(
                free_cash_flow,
                operating_profit,
            )
        )

    # ========================================================
    # CAGR
    # ========================================================

    cagr = calculate_all_cagrs(
        pnl,
        company_id,
        year,
    )

    revenue_cagr_5yr = cagr[
        "revenue_cagr_5yr"
    ]

    pat_cagr_5yr = cagr[
        "pat_cagr_5yr"
    ]

    eps_cagr_5yr = cagr[
        "eps_cagr_5yr"
    ]

    # ========================================================
    # BOOK VALUE PER SHARE
    # ========================================================

    company = companies.get(
        company_id,
        {},
    )

    book_value_per_share = company.get(
        "book_value"
    )

    # ========================================================
    # COMPOSITE QUALITY SCORE
    # ========================================================

    # Calculated separately after all
    # company-year KPI values are available.

    composite_quality_score = None

    # ========================================================
    # TOTAL DEBT
    # ========================================================

    total_debt = borrowings

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "company_id": company_id,
        "year": year,

        # ----------------------------------------------------
        # Profitability
        # ----------------------------------------------------

        "net_profit_margin": npm,

        "operating_profit_margin": opm,

        "return_on_equity": roe,

        "return_on_capital": roce,

        "return_on_assets": roa,

        # ----------------------------------------------------
        # Leverage
        # ----------------------------------------------------

        "debt_to_equity": debt_to_equity,

        "high_leverage_flag": int(
            high_leverage_flag
        ),

        # ----------------------------------------------------
        # Interest Coverage
        # ----------------------------------------------------

        "interest_coverage": interest_coverage,

        "icr_warning_flag": int(
            icr_warning_flag
        ),

        "icr_label": icr_label,

        # ----------------------------------------------------
        # Efficiency
        # ----------------------------------------------------

        "asset_turnover": asset_turnover,

        # ----------------------------------------------------
        # Cash Flow
        # ----------------------------------------------------

        "free_cash_flow": free_cash_flow,

        "cash_from_operations_cr":
            cash_from_operations,

        "capex_cr": capex,

        # ----------------------------------------------------
        # Earnings
        # ----------------------------------------------------

        "earnings_per_share": eps,

        "book_value_per_share":
            book_value_per_share,

        "dividend_payout_ratio_pct":
            dividend_payout,

        # ----------------------------------------------------
        # Debt
        # ----------------------------------------------------

        "total_debt_cr": total_debt,

        # ----------------------------------------------------
        # Existing CAGR fields
        # ----------------------------------------------------

        "revenue_cagr":
            revenue_cagr_5yr,

        "pat_cagr":
            pat_cagr_5yr,

        "eps_cagr":
            eps_cagr_5yr,

        # ----------------------------------------------------
        # 5-year CAGR
        # ----------------------------------------------------

        "revenue_cagr_5yr":
            revenue_cagr_5yr,

        "pat_cagr_5yr":
            pat_cagr_5yr,

        "eps_cagr_5yr":
            eps_cagr_5yr,

        # ----------------------------------------------------
        # Composite
        # ----------------------------------------------------

        "composite_quality_score":
            composite_quality_score,

        # ----------------------------------------------------
        # 3-year CAGR
        # ----------------------------------------------------

        "revenue_cagr_3yr":
            cagr["revenue_cagr_3yr"],

        "revenue_cagr_3yr_flag":
            cagr["revenue_cagr_3yr_flag"],

        "pat_cagr_3yr":
            cagr["pat_cagr_3yr"],

        "pat_cagr_3yr_flag":
            cagr["pat_cagr_3yr_flag"],

        "eps_cagr_3yr":
            cagr["eps_cagr_3yr"],

        "eps_cagr_3yr_flag":
            cagr["eps_cagr_3yr_flag"],

        # ----------------------------------------------------
        # 5-year CAGR flags
        # ----------------------------------------------------

        "revenue_cagr_5yr_flag":
            cagr["revenue_cagr_5yr_flag"],

        "pat_cagr_5yr_flag":
            cagr["pat_cagr_5yr_flag"],

        "eps_cagr_5yr_flag":
            cagr["eps_cagr_5yr_flag"],

        # ----------------------------------------------------
        # 10-year CAGR
        # ----------------------------------------------------

        "revenue_cagr_10yr":
            cagr["revenue_cagr_10yr"],

        "revenue_cagr_10yr_flag":
            cagr["revenue_cagr_10yr_flag"],

        "pat_cagr_10yr":
            cagr["pat_cagr_10yr"],

        "pat_cagr_10yr_flag":
            cagr["pat_cagr_10yr_flag"],

        "eps_cagr_10yr":
            cagr["eps_cagr_10yr"],

        "eps_cagr_10yr_flag":
            cagr["eps_cagr_10yr_flag"],
    }


# ============================================================
# POPULATE FINANCIAL RATIOS
# ============================================================

def populate_financial_ratios():
    """Populate financial_ratios table."""

    conn = get_connection()

    try:

        # ----------------------------------------------------
        # Load company master data
        # ----------------------------------------------------

        companies = load_company_data()

        # ----------------------------------------------------
        # Load source data
        # ----------------------------------------------------

        (
            pnl,
            balance_sheet,
            cashflow,
            sectors,
        ) = load_source_data(conn)

        # ----------------------------------------------------
        # Calculate rows
        # ----------------------------------------------------

        rows = []

        for company_id, year in pnl.keys():

            result = calculate_row(
                company_id,
                year,
                pnl,
                balance_sheet,
                cashflow,
                sectors,
                companies,
            )

            rows.append(result)

        print(
            f"Rows calculated: {len(rows)}"
        )

        print()

        # ----------------------------------------------------
        # Clear existing rows
        # ----------------------------------------------------

        conn.execute(
            "DELETE FROM financial_ratios"
        )

        # ====================================================
        # COLUMNS
        # ====================================================

        columns = [

            "company_id",
            "year",

            # Profitability
            "net_profit_margin",
            "operating_profit_margin",
            "return_on_equity",
            "return_on_capital",
            "return_on_assets",

            # Leverage
            "debt_to_equity",
            "high_leverage_flag",

            # Interest Coverage
            "interest_coverage",
            "icr_warning_flag",
            "icr_label",

            # Efficiency
            "asset_turnover",

            # Cash Flow
            "free_cash_flow",
            "cash_from_operations_cr",
            "capex_cr",

            # Earnings
            "earnings_per_share",
            "book_value_per_share",
            "dividend_payout_ratio_pct",

            # Debt
            "total_debt_cr",

            # Existing CAGR fields
            "revenue_cagr",
            "pat_cagr",
            "eps_cagr",

            # 5-year CAGR
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "eps_cagr_5yr",

            # Composite
            "composite_quality_score",

            # 3-year CAGR
            "revenue_cagr_3yr",
            "revenue_cagr_3yr_flag",

            "pat_cagr_3yr",
            "pat_cagr_3yr_flag",

            "eps_cagr_3yr",
            "eps_cagr_3yr_flag",

            # 5-year CAGR flags
            "revenue_cagr_5yr_flag",
            "pat_cagr_5yr_flag",
            "eps_cagr_5yr_flag",

            # 10-year CAGR
            "revenue_cagr_10yr",
            "revenue_cagr_10yr_flag",

            "pat_cagr_10yr",
            "pat_cagr_10yr_flag",

            "eps_cagr_10yr",
            "eps_cagr_10yr_flag",
        ]

        # ----------------------------------------------------
        # Safety check
        # ----------------------------------------------------

        print(
            f"Columns to insert: {len(columns)}"
        )

        placeholders = ", ".join(
            ["?"] * len(columns)
        )

        column_sql = ", ".join(
            columns
        )

        insert_sql = f"""
        INSERT INTO financial_ratios (
            {column_sql}
        )
        VALUES (
            {placeholders}
        )
        """

        # ----------------------------------------------------
        # Build values
        # ----------------------------------------------------

        values = []

        for r in rows:

            row_values = tuple(
                r.get(column)
                for column in columns
            )

            values.append(
                row_values
            )

        # ----------------------------------------------------
        # Verify column/value count
        # ----------------------------------------------------

        if values:

            print(
                f"Values per row: "
                f"{len(values[0])}"
            )

            if (
                len(values[0])
                != len(columns)
            ):

                raise ValueError(
                    f"Column/value mismatch: "
                    f"{len(columns)} columns but "
                    f"{len(values[0])} values"
                )

        # ----------------------------------------------------
        # Insert
        # ----------------------------------------------------

        conn.executemany(
            insert_sql,
            values,
        )

        conn.commit()

        # ====================================================
        # VERIFICATION
        # ====================================================

        count = conn.execute(
            """
            SELECT COUNT(*)
            FROM financial_ratios
            """
        ).fetchone()[0]

        companies_count = conn.execute(
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
        print(
            "FINANCIAL RATIO ENGINE COMPLETED"
        )
        print("=" * 60)

        print(
            f"Rows inserted: {count}"
        )

        print(
            f"Companies covered: "
            f"{companies_count}"
        )

        print(
            f"Year range: "
            f"{year_range[0]} - "
            f"{year_range[1]}"
        )

        print("=" * 60)

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    populate_financial_ratios()