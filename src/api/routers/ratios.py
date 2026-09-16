from fastapi import APIRouter, HTTPException
from src.api.database import get_db_connection

router = APIRouter(prefix="/companies", tags=["Financial Ratios"])


@router.get("/{ticker}/ratios")
def get_financial_ratios(ticker: str):
    """Return financial ratio data for one company."""
    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
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
            FROM financial_ratios
            WHERE company_id = ?
            ORDER BY year DESC
            """,
            (ticker.upper(),),
        ).fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Financial ratio data for '{ticker.upper()}' not found",
            )

        return [dict(row) for row in rows]

    finally:
        connection.close()