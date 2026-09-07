import csv
import sqlite3
from pathlib import Path

from src.analytics.cashflow_kpis import classify_capital_allocation


DB_PATH = Path("data/nifty100.db")
OUTPUT_PATH = Path("output/capital_allocation.csv")


def sign(value):
    """Return +, -, or None based on the value."""
    if value is None:
        return None

    if value > 0:
        return "+"

    if value < 0:
        return "-"

    return "0"


def calculate_cfo_pat_ratio(conn, company_id, year):
    """
    Calculate CFO/PAT ratio for the current year.

    Returns None when PAT is missing or zero.
    """
    row = conn.execute(
        """
        SELECT
            c.operating_activity,
            p.net_profit
        FROM cashflow c
        LEFT JOIN profitandloss p
            ON c.company_id = p.company_id
            AND c.year = p.year
        WHERE c.company_id = ?
          AND c.year = ?
        """,
        (company_id, year),
    ).fetchone()

    if row is None:
        return None

    cfo, pat = row

    if cfo is None or pat is None or pat == 0:
        return None

    return cfo / pat


def generate_capital_allocation():
    """Generate capital allocation classification for every company-year."""

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)

    try:
        rows = conn.execute(
            """
            SELECT
                company_id,
                year,
                operating_activity,
                investing_activity,
                financing_activity
            FROM cashflow
            ORDER BY company_id, year
            """
        ).fetchall()

        output_rows = []

        for (
            company_id,
            year,
            cfo,
            cfi,
            cff,
        ) in rows:

            cfo_sign = sign(cfo)
            cfi_sign = sign(cfi)
            cff_sign = sign(cff)

            cfo_pat_ratio = calculate_cfo_pat_ratio(
                conn,
                company_id,
                year,
            )

            if (
                cfo_sign is None
                or cfi_sign is None
                or cff_sign is None
            ):
                pattern_label = "Unknown"
            else:
                pattern_label = classify_capital_allocation(
                    cfo_sign,
                    cfi_sign,
                    cff_sign,
                    cfo_pat_ratio,
                )

            output_rows.append(
                {
                    "company_id": company_id,
                    "year": year,
                    "cfo_sign": cfo_sign,
                    "cfi_sign": cfi_sign,
                    "cff_sign": cff_sign,
                    "pattern_label": pattern_label,
                }
            )

        with open(
            OUTPUT_PATH,
            "w",
            newline="",
            encoding="utf-8",
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=[
                    "company_id",
                    "year",
                    "cfo_sign",
                    "cfi_sign",
                    "cff_sign",
                    "pattern_label",
                ],
            )

            writer.writeheader()
            writer.writerows(output_rows)

        print("=" * 60)
        print("CAPITAL ALLOCATION ANALYSIS COMPLETED")
        print("=" * 60)
        print(f"Rows written: {len(output_rows)}")
        print(f"Output file: {OUTPUT_PATH}")
        print("=" * 60)

    finally:
        conn.close()


if __name__ == "__main__":
    generate_capital_allocation()