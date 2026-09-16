from fastapi import APIRouter, HTTPException

from src.api.database import get_db_connection
from src.analytics.peer_comparison import (
    load_data,
    prepare_company_data,
    build_peer_sheet,
)

router = APIRouter(prefix="/peers", tags=["Peers"])


@router.get("/{ticker}")
def get_peers(ticker: str):
    """Return peer companies for a ticker."""
    ticker = ticker.upper()
    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                pg.peer_group_name,
                pg.company_id,
                c.company_name,
                pg.is_benchmark
            FROM peer_groups pg
            JOIN companies c
                ON pg.company_id = c.id
            WHERE pg.peer_group_name IN (
                SELECT peer_group_name
                FROM peer_groups
                WHERE company_id = ?
            )
            ORDER BY pg.peer_group_name, pg.company_id
            """,
            (ticker,),
        ).fetchall()

        if not rows:
            raise HTTPException(
                status_code=404,
                detail=f"Peer group for '{ticker}' not found",
            )

        return [dict(row) for row in rows]
    finally:
        connection.close()


@router.get("/{ticker}/compare")
def compare_peers(ticker: str):
    """Return detailed peer comparison for a company."""
    ticker = ticker.upper()

    (
    percentile_df,
    peer_group_df,
    ratios_df,
    pnl_df,
    market_df,
) = load_data()

    company_data = prepare_company_data(
        percentile_df,
        ratios_df,
        pnl_df,
        market_df,
    )

    company_groups = peer_group_df[
        peer_group_df["company_id"] == ticker
    ]

    if company_groups.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Peer group for '{ticker}' not found",
        )

    peer_group = company_groups.iloc[0]["peer_group_name"]

    result = build_peer_sheet(
        peer_group,
        percentile_df,
        peer_group_df,
        company_data,
    )

    if result is None or result.empty:
        raise HTTPException(
            status_code=404,
            detail=f"Peer comparison for '{ticker}' not found",
        )

    result = result.replace({float("nan"): None})

    return result.to_dict(orient="records")