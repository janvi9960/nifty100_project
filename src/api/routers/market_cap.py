from fastapi import APIRouter, HTTPException

from src.api.database import get_db_connection

router = APIRouter(prefix="/market-cap", tags=["Market Cap"])


@router.get("")
def get_market_cap():
    """Return latest market-cap data for all companies."""
    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                mc.company_id,
                c.company_name,
                mc.year,
                mc.market_cap_crore,
                mc.enterprise_value_crore,
                mc.pe_ratio,
                mc.pb_ratio,
                mc.ev_ebitda,
                mc.dividend_yield_pct
            FROM market_cap mc
            JOIN companies c
                ON mc.company_id = c.id
            WHERE mc.year = (
                SELECT MAX(mc2.year)
                FROM market_cap mc2
                WHERE mc2.company_id = mc.company_id
            )
            ORDER BY mc.market_cap_crore DESC
            """
        ).fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="Market-cap data not found",
            )

        return [dict(row) for row in rows]

    finally:
        connection.close()