from fastapi import APIRouter, HTTPException

from src.api.database import get_db_connection

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("")
def get_documents():
    """Return available company documents."""
    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                d.document_id,
                d.company_id,
                c.company_name,
                d.year,
                d.document_url
            FROM documents d
            LEFT JOIN companies c
                ON d.company_id = c.id
            ORDER BY d.company_id, d.year DESC
            """
        ).fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail="Documents not found",
            )

        return [dict(row) for row in rows]

    finally:
        connection.close()


@router.get("/{ticker}")
def get_company_documents(ticker: str):
    """Return documents for a specific company."""
    ticker = ticker.upper()
    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                d.document_id,
                d.company_id,
                c.company_name,
                d.year,
                d.document_url
            FROM documents d
            LEFT JOIN companies c
                ON d.company_id = c.id
            WHERE d.company_id = ?
            ORDER BY d.year DESC
            """,
            (ticker,),
        ).fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Documents for '{ticker}' not found",
            )

        return [dict(row) for row in rows]

    finally:
        connection.close()