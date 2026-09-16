from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


PROJECT_ROOT = Path(__file__).resolve().parents[3]
TEARSHEET_DIR = PROJECT_ROOT / "reports" / "tearsheets"

router = APIRouter(prefix="/companies", tags=["Tearsheet"])


@router.get("/{ticker}/tearsheet")
def get_tearsheet(ticker: str):
    """Return the PDF tearsheet for one company."""
    ticker = ticker.upper()

    pdf_path = TEARSHEET_DIR / f"{ticker}_tearsheet.pdf"

    if not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Tearsheet for '{ticker}' not found",
        )

    return FileResponse(
        path=pdf_path,
        media_type="application/pdf",
        filename=f"{ticker}_tearsheet.pdf",
    )