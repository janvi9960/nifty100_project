from fastapi import APIRouter, HTTPException
from src.api.database import get_db_connection

router = APIRouter(prefix="/companies", tags=["Balance Sheet"])


@router.get("/{ticker}/bs")
def get_balance_sheet(ticker: str):
    """Return balance sheet data for one company."""
    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                company_id,
                year,
                borrowings,
                total_assets,
                equity,
                reserves
            FROM balancesheet
            WHERE company_id = ?
            ORDER BY year DESC
            """,
            (ticker.upper(),),
        ).fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Balance Sheet data for '{ticker.upper()}' not found",
            )

        return [dict(row) for row in rows]

    finally:
        connection.close()