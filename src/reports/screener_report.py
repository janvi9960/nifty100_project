import sqlite3
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "screener"
OUTPUT_FILE = OUTPUT_DIR / "nifty100_screener_report.pdf"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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


def load_data():
    conn = sqlite3.connect(DB_PATH)

    ratios_query = """
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
            fr.interest_coverage
        FROM financial_ratios fr
        JOIN companies co
            ON fr.company_id = co.id
        LEFT JOIN sectors s
            ON fr.company_id = s.company_id
        WHERE fr.year = (
            SELECT MAX(year)
            FROM financial_ratios
        )
    """

    valuation_query = """
        SELECT
            company_id,
            pe_ratio,
            pb_ratio,
            dividend_yield_pct
        FROM market_cap
        WHERE year = (
            SELECT MAX(year)
            FROM market_cap
        )
    """

    data = pd.read_sql_query(ratios_query, conn)
    valuation = pd.read_sql_query(valuation_query, conn)

    conn.close()

    data = data.merge(
        valuation,
        on="company_id",
        how="left",
    )

    return data


def apply_min_filter(df, column, value):
    if column not in df.columns:
        return df

    return df[
        df[column].isna() |
        (df[column] >= value)
    ]


def apply_max_filter(df, column, value):
    if column not in df.columns:
        return df

    return df[
        df[column].isna() |
        (df[column] <= value)
    ]


def apply_preset(data, preset):
    filtered = data.copy()

    filtered = apply_min_filter(
        filtered, "return_on_equity", preset["roe_min"]
    )
    filtered = apply_max_filter(
        filtered, "debt_to_equity", preset["de_max"]
    )
    filtered = apply_min_filter(
        filtered, "free_cash_flow", preset["fcf_min"]
    )
    filtered = apply_min_filter(
        filtered, "revenue_cagr_5yr", preset["revenue_cagr_min"]
    )
    filtered = apply_min_filter(
        filtered, "pat_cagr_5yr", preset["pat_cagr_min"]
    )
    filtered = apply_min_filter(
        filtered, "operating_profit_margin", preset["opm_min"]
    )
    filtered = apply_max_filter(
        filtered, "pe_ratio", preset["pe_max"]
    )
    filtered = apply_max_filter(
        filtered, "pb_ratio", preset["pb_max"]
    )
    filtered = apply_min_filter(
        filtered, "dividend_yield_pct", preset["dividend_min"]
    )
    filtered = apply_min_filter(
        filtered, "interest_coverage", preset["icr_min"]
    )

    return filtered.sort_values(
        ["composite_quality_score", "company_id"],
        ascending=[False, True],
    )


def fmt(value, decimals=2):
    if pd.isna(value):
        return "N/A"
    return f"{value:.{decimals}f}"


def criteria_table(preset):
    rows = [
        ["Metric", "Requirement"],
        ["ROE", f">= {preset['roe_min']:.1f}%"],
        ["Debt / Equity", f"<= {preset['de_max']:.1f}"],
        ["Free Cash Flow", f">= {preset['fcf_min']:,.0f} Cr"],
        ["Revenue CAGR (5yr)", f">= {preset['revenue_cagr_min']:.1f}%"],
        ["PAT CAGR (5yr)", f">= {preset['pat_cagr_min']:.1f}%"],
        ["Operating Profit Margin", f">= {preset['opm_min']:.1f}%"],
        ["P/E", f"<= {preset['pe_max']:.1f}"],
        ["P/B", f"<= {preset['pb_max']:.1f}"],
        ["Dividend Yield", f">= {preset['dividend_min']:.1f}%"],
        ["Interest Coverage", f">= {preset['icr_min']:.1f}"],
    ]
    return rows


def company_table(filtered):
    rows = [[
        "Rank",
        "Ticker",
        "Company",
        "Sector",
        "Quality",
        "ROE %",
        "D/E",
        "Rev CAGR %",
        "PAT CAGR %",
        "P/E",
        "P/B",
    ]]

    for rank, (_, row) in enumerate(filtered.iterrows(), start=1):
        rows.append([
            str(rank),
            str(row["company_id"]),
            str(row["company_name"]),
            str(row["broad_sector"] or "N/A"),
            fmt(row["composite_quality_score"]),
            fmt(row["return_on_equity"]),
            fmt(row["debt_to_equity"]),
            fmt(row["revenue_cagr_5yr"]),
            fmt(row["pat_cagr_5yr"]),
            fmt(row["pe_ratio"]),
            fmt(row["pb_ratio"]),
        ])

    return rows


def build_report():
    data = load_data()

    if len(data) != 92:
        raise ValueError(
            f"Expected 92 companies, found {len(data)}."
        )

    report_year = int(data["year"].max())

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=9,
        alignment=TA_CENTER,
        textColor=colors.grey,
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "PresetHeading",
        parent=styles["Heading1"],
        fontSize=16,
        leading=19,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontSize=7,
        leading=8,
    )

    doc = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title="Nifty 100 Screener Report",
        author="Nifty100 Financial Intelligence Project",
    )

    story = []

    story.append(Paragraph(
        "NIFTY 100 — SCREENER REPORT",
        title_style,
    ))

    story.append(Paragraph(
        f"Latest available financial year: {report_year} | "
        f"Universe: {len(data)} companies | "
        "Screening logic aligned with the Streamlit Screener",
        subtitle_style,
    ))

    overview_rows = [
        ["Preset", "Companies Found", "Match %"],
    ]

    preset_results = {}

    for name, preset in PRESETS.items():
        filtered = apply_preset(data, preset)
        count = len(filtered)
        pct = count / len(data) * 100

        preset_results[name] = filtered

        overview_rows.append([
            name,
            str(count),
            f"{pct:.1f}%",
        ])

    overview = Table(
        overview_rows,
        colWidths=[70 * mm, 45 * mm, 35 * mm],
        repeatRows=1,
    )

    overview.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.whitesmoke, colors.lightgrey]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    story.append(overview)
    story.append(Spacer(1, 8 * mm))

    story.append(Paragraph(
        "Interpretation: missing metric values are treated as pass-through "
        "for consistency with the existing dashboard screener.",
        small_style,
    ))

    for index, (name, preset) in enumerate(PRESETS.items()):
        filtered = preset_results[name]

        story.append(PageBreak())

        story.append(Paragraph(
            f"{name} Screener",
            heading_style,
        ))

        count = len(filtered)
        pct = count / len(data) * 100

        story.append(Paragraph(
            f"<b>{count}</b> of {len(data)} companies matched "
            f"({pct:.1f}%). Results are ranked by composite quality score.",
            body_style,
        ))

        story.append(Spacer(1, 4 * mm))

        crit = Table(
            criteria_table(preset),
            colWidths=[50 * mm, 55 * mm],
        )

        crit.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5b9bd5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.whitesmoke]),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))

        story.append(crit)
        story.append(Spacer(1, 5 * mm))

        table_data = company_table(filtered)

        result_table = Table(
            table_data,
            colWidths=[
                10 * mm,
                19 * mm,
                55 * mm,
                38 * mm,
                18 * mm,
                19 * mm,
                15 * mm,
                23 * mm,
                23 * mm,
                17 * mm,
                17 * mm,
            ],
            repeatRows=1,
        )

        result_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f4e78")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 6.5),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.whitesmoke]),
            ("ALIGN", (0, 0), (1, -1), "CENTER"),
            ("ALIGN", (4, 1), (-1, -1), "RIGHT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))

        story.append(result_table)

    doc.build(story)

    return OUTPUT_FILE


if __name__ == "__main__":
    output = build_report()
    print(f"Generated: {output}")
    print(f"Size: {output.stat().st_size:,} bytes")
