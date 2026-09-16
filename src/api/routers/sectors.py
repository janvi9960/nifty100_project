from fastapi import APIRouter
from src.api.database import get_db_connection

router = APIRouter(prefix="/sectors", tags=["Sectors"])


@router.get("")
def get_sectors():
    """Return all sectors with company counts."""
    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                broad_sector,
                COUNT(DISTINCT company_id) AS company_count
            FROM sectors
            GROUP BY broad_sector
            ORDER BY broad_sector
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


@router.get("/{sector}/companies")
def get_sector_companies(sector: str):
    """Return companies belonging to a sector."""
    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                s.company_id,
                c.company_name,
                s.broad_sector,
                s.sub_sector
            FROM sectors s
            JOIN companies c
                ON s.company_id = c.id
            WHERE LOWER(s.broad_sector) = LOWER(?)
            ORDER BY s.company_id
            """,
            (sector,),
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()