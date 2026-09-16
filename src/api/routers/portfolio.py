from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PORTFOLIO_STATS_PATH = PROJECT_ROOT / "output" / "portfolio_stats.csv"


@router.get("/stats")
def get_portfolio_stats():
    """Return portfolio-level statistics for key financial metrics."""
    if not PORTFOLIO_STATS_PATH.exists():
        raise HTTPException(
            status_code=404,
            detail="Portfolio statistics file not found",
        )

    try:
        df = pd.read_csv(PORTFOLIO_STATS_PATH)

        if df.empty:
            raise HTTPException(
                status_code=404,
                detail="Portfolio statistics are empty",
            )

        metric_column = df.columns[0]

        records = []
        for _, row in df.iterrows():
            records.append({
                "metric": row[metric_column],
                "P10": row["P10"],
                "P25": row["P25"],
                "P50": row["P50"],
                "P75": row["P75"],
                "P90": row["P90"],
                "Mean": row["Mean"],
                "Std": row["Std"],
            })

        return records

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load portfolio statistics: {exc}",
        )