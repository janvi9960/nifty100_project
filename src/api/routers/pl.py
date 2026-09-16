from fastapi import APIRouter, HTTPException
from src.api.database import get_db_connection

router = APIRouter(prefix="/companies", tags=["Profit & Loss"])


@router.get("/{ticker}/pl")
def get_profit_and_loss(ticker: str):
    """Return profit and loss data for one company."""
    connection = get_db_connection()

    try:
        rows = connection.execute(
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
            WHERE company_id = ?
            ORDER BY year DESC
            """,
            (ticker.upper(),),
        ).fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"P&L data for '{ticker.upper()}' not found",
            )

        return [dict(row) for row in rows]

    finally:
        connection.close()