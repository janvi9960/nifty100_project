from fastapi import APIRouter, HTTPException
from src.api.database import get_db_connection

router = APIRouter(prefix="/companies", tags=["Companies"])


@router.get("")
def get_companies():
    """Return all Nifty100 companies."""
    connection = get_db_connection()

    try:
        rows = connection.execute(
            "SELECT id, company_name FROM companies ORDER BY id"
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


@router.get("/{ticker}")
def get_company(ticker: str):
    """Return details for one company."""
    connection = get_db_connection()

    try:
        row = connection.execute(
            "SELECT id, company_name FROM companies WHERE id = ?",
            (ticker.upper(),),
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{ticker.upper()}' not found",
            )

        return dict(row)

    finally:
        connection.close()
