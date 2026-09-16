from fastapi import APIRouter, HTTPException
from src.api.database import get_db_connection

router = APIRouter(prefix="/companies", tags=["Cash Flow"])


@router.get("/{ticker}/cashflow")
def get_cash_flow(ticker: str):
    """Return cash flow data for one company."""
    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                company_id,
                year,
                operating_activity,
                investing_activity,
                financing_activity
            FROM cashflow
            WHERE company_id = ?
            ORDER BY year DESC
            """,
            (ticker.upper(),),
        ).fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Cash Flow data for '{ticker.upper()}' not found",
            )

        return [dict(row) for row in rows]

    finally:
        connection.close()