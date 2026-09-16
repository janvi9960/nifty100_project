from fastapi import APIRouter, HTTPException

from src.analytics.valuation import build_valuation_summary

router = APIRouter(prefix="/valuation", tags=["Valuation"])


@router.get("")
def get_valuation():
    """Return valuation summary for all companies."""
    try:
        summary = build_valuation_summary()

        if summary is None or summary.empty:
            raise HTTPException(
                status_code=404,
                detail="Valuation data not found",
            )

        summary = summary.astype(object).where(summary.notna(), None)

        return summary.to_dict(orient="records")

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unable to load valuation data: {exc}",
        )