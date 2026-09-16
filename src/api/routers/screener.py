import sqlite3
from pathlib import Path

from fastapi import APIRouter, HTTPException

from src.api.database import get_db_connection


PROJECT_ROOT = Path(__file__).resolve().parents[3]

router = APIRouter(prefix="/screener", tags=["Screener"])


PRESETS = {
    "Quality": {
        "roe_min": 15.0,
        "de_max": 1.0,
        "fcf_min": 0.0,
        "revenue_cagr_min": 8.0,
        "pat_cagr_min": 8.0,
        "opm_min": 10.0,
        "pe_max": 60.0,
        "pb_max": 10.0,
        "dividend_min": 0.0,
        "icr_min": 5.0,
    },
    "Value": {
        "roe_min": 8.0,
        "de_max": 2.0,
        "fcf_min": 0.0,
        "revenue_cagr_min": -10.0,
        "pat_cagr_min": -10.0,
        "opm_min": -10.0,
        "pe_max": 20.0,
        "pb_max": 3.0,
        "dividend_min": 0.0,
        "icr_min": 2.0,
    },
    "Growth": {
        "roe_min": 12.0,
        "de_max": 2.0,
        "fcf_min": -10000.0,
        "revenue_cagr_min": 15.0,
        "pat_cagr_min": 12.0,
        "opm_min": 5.0,
        "pe_max": 100.0,
        "pb_max": 20.0,
        "dividend_min": 0.0,
        "icr_min": 2.0,
    },
    "Dividend": {
        "roe_min": 8.0,
        "de_max": 2.0,
        "fcf_min": 0.0,
        "revenue_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 80.0,
        "pb_max": 15.0,
        "dividend_min": 2.0,
        "icr_min": 2.0,
    },
    "Debt-Free": {
        "roe_min": 8.0,
        "de_max": 0.1,
        "fcf_min": 0.0,
        "revenue_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 100.0,
        "pb_max": 20.0,
        "dividend_min": 0.0,
        "icr_min": 0.0,
    },
    "Turnaround": {
        "roe_min": 0.0,
        "de_max": 3.0,
        "fcf_min": -10000.0,
        "revenue_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": -10.0,
        "pe_max": 100.0,
        "pb_max": 20.0,
        "dividend_min": 0.0,
        "icr_min": 0.0,
    },
}


def apply_min_filter(rows, column, value):
    return [
        row for row in rows
        if row[column] is None or row[column] >= value
    ]


def apply_max_filter(rows, column, value):
    return [
        row for row in rows
        if row[column] is None or row[column] <= value
    ]


@router.get("")
def run_screener(preset: str = "Quality"):
    """Run the Nifty100 screener using a predefined preset."""

    if preset not in PRESETS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid preset '{preset}'. "
                   f"Available presets: {list(PRESETS.keys())}",
        )

    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                fr.company_id,
                co.company_name,
                s.broad_sector,
                fr.year,
                fr.composite_quality_score,
                fr.return_on_equity,
                fr.debt_to_equity,
                fr.free_cash_flow,
                fr.revenue_cagr_5yr,
                fr.pat_cagr_5yr,
                fr.operating_profit_margin,
                fr.interest_coverage,
                mc.pe_ratio,
                mc.pb_ratio,
                mc.dividend_yield_pct
            FROM financial_ratios fr
            JOIN companies co
                ON fr.company_id = co.id
            LEFT JOIN sectors s
                ON fr.company_id = s.company_id
            LEFT JOIN market_cap mc
                ON fr.company_id = mc.company_id
                AND mc.year = (
                    SELECT MAX(year)
                    FROM market_cap
                )
            WHERE fr.year = (
                SELECT MAX(year)
                FROM financial_ratios
            )
            """
        ).fetchall()

        results = [dict(row) for row in rows]
        criteria = PRESETS[preset]

        results = apply_min_filter(
            results, "return_on_equity", criteria["roe_min"]
        )
        results = apply_max_filter(
            results, "debt_to_equity", criteria["de_max"]
        )
        results = apply_min_filter(
            results, "free_cash_flow", criteria["fcf_min"]
        )
        results = apply_min_filter(
            results, "revenue_cagr_5yr", criteria["revenue_cagr_min"]
        )
        results = apply_min_filter(
            results, "pat_cagr_5yr", criteria["pat_cagr_min"]
        )
        results = apply_min_filter(
            results, "operating_profit_margin", criteria["opm_min"]
        )
        results = apply_max_filter(
            results, "pe_ratio", criteria["pe_max"]
        )
        results = apply_max_filter(
            results, "pb_ratio", criteria["pb_max"]
        )
        results = apply_min_filter(
            results, "dividend_yield_pct", criteria["dividend_min"]
        )
        results = apply_min_filter(
            results, "interest_coverage", criteria["icr_min"]
        )

        results.sort(
            key=lambda row: (
                row["composite_quality_score"] is None,
                -(row["composite_quality_score"] or 0),
                row["company_id"],
            )
        )

        return {
            "preset": preset,
            "total_companies": len(rows),
            "matched_companies": len(results),
            "results": results,
        }

    finally:
        connection.close()