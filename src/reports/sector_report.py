from pathlib import Path
import re
import sqlite3

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    KeepTogether,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "sector"

LATEST_YEAR = 2024

KPI_COLUMNS = [
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "return_on_equity",
    "return_on_capital",
    "net_profit_margin",
    "debt_to_equity",
    "interest_coverage",
    "composite_quality_score",
]

KPI_LABELS = {
    "revenue_cagr_5yr": "Revenue CAGR (5Y)",
    "pat_cagr_5yr": "PAT CAGR (5Y)",
    "return_on_equity": "ROE",
    "return_on_capital": "ROCE",
    "net_profit_margin": "Net Profit Margin",
    "debt_to_equity": "Debt / Equity",
    "interest_coverage": "Interest Coverage",
    "composite_quality_score": "Quality Score",
}


def get_connection():
    return sqlite3.connect(DB_PATH)


def safe_filename(value):
    value = re.sub(r"[^\w\s-]", "", str(value))
    value = re.sub(r"\s+", "_", value.strip())
    return value


def load_sector_data():
    query = """
        SELECT
            s.broad_sector,
            c.id AS company_id,
            c.company_name,
            fr.year,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            fr.return_on_equity,
            fr.return_on_capital,
            fr.net_profit_margin,
            fr.debt_to_equity,
            fr.interest_coverage,
            fr.composite_quality_score
        FROM sectors s
        JOIN companies c
            ON s.company_id = c.id
        JOIN financial_ratios fr
            ON s.company_id = fr.company_id
        WHERE fr.year = ?
        ORDER BY s.broad_sector, c.id
    """

    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=[LATEST_YEAR])


def calculate_sector_medians(sector_df):
    return sector_df[KPI_COLUMNS].median(numeric_only=True)


def get_best_worst(sector_df):
    valid = sector_df.dropna(subset=["composite_quality_score"])

    if valid.empty:
        return None, None

    best = valid.loc[valid["composite_quality_score"].idxmax()]
    worst = valid.loc[valid["composite_quality_score"].idxmin()]

    return best, worst


def fmt(value, suffix=""):
    if pd.isna(value):
        return "N/A"
    return f"{float(value):.2f}{suffix}"


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="SectorTitle",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            spaceAfter=5 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Subtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
            spaceAfter=7 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionHeading",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            alignment=TA_LEFT,
            spaceBefore=3 * mm,
            spaceAfter=3 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=7.5,
            leading=9,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SmallCenter",
            parent=styles["Small"],
            alignment=TA_CENTER,
        )
    )

    return styles


def make_median_table(medians, styles):
    rows = [["KPI", "Sector Median"]]

    for column in KPI_COLUMNS:
        value = medians[column]

        if column in {
            "revenue_cagr_5yr",
            "pat_cagr_5yr",
            "return_on_equity",
            "return_on_capital",
            "net_profit_margin",
        }:
            display = fmt(value, "%")
        else:
            display = fmt(value)

        rows.append([KPI_LABELS[column], display])

    table = Table(
        rows,
        colWidths=[105 * mm, 55 * mm],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B7B7B7")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F4F7FA"),
                ]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    return table


def make_best_worst_table(best, worst):
    best_name = str(best["company_name"]).replace("\n", " ") if best is not None else "N/A"
    worst_name = str(worst["company_name"]).replace("\n", " ") if worst is not None else "N/A"

    rows = [
        ["Category", "Company", "Ticker", "Quality Score"],
        [
            "Best",
            best_name,
            str(best["company_id"]) if best is not None else "N/A",
            fmt(best["composite_quality_score"]) if best is not None else "N/A",
        ],
        [
            "Worst",
            worst_name,
            str(worst["company_id"]) if worst is not None else "N/A",
            fmt(worst["composite_quality_score"]) if worst is not None else "N/A",
        ],
    ]

    table = Table(
        rows,
        colWidths=[28 * mm, 88 * mm, 25 * mm, 34 * mm],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B7B7B7")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#EAF4EA")),
                ("BACKGROUND", (0, 2), (-1, 2), colors.HexColor("#FBEAEA")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    return table


def make_company_table(sector_df):
    columns = [
        ("company_id", "Ticker"),
        ("company_name", "Company"),
        ("revenue_cagr_5yr", "Rev CAGR"),
        ("pat_cagr_5yr", "PAT CAGR"),
        ("return_on_equity", "ROE"),
        ("return_on_capital", "ROCE"),
        ("net_profit_margin", "NPM"),
        ("debt_to_equity", "D/E"),
        ("composite_quality_score", "Quality"),
    ]

    rows = [[label for _, label in columns]]

    for _, row in sector_df.sort_values(
        "composite_quality_score",
        ascending=False,
        na_position="last",
    ).iterrows():

        name = str(row["company_name"]).replace("\n", " ")

        rows.append(
            [
                str(row["company_id"]),
                Paragraph(name, build_styles()["Small"]),
                fmt(row["revenue_cagr_5yr"], "%"),
                fmt(row["pat_cagr_5yr"], "%"),
                fmt(row["return_on_equity"], "%"),
                fmt(row["return_on_capital"], "%"),
                fmt(row["net_profit_margin"], "%"),
                fmt(row["debt_to_equity"]),
                fmt(row["composite_quality_score"]),
            ]
        )

    table = Table(
        rows,
        colWidths=[
            19 * mm,
            50 * mm,
            17 * mm,
            17 * mm,
            15 * mm,
            15 * mm,
            15 * mm,
            15 * mm,
            18 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 6.5),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 6.5),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),
                ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B7B7B7")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                    colors.white,
                    colors.HexColor("#F7F9FB"),
                ]),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    return table


def add_page_number(canvas, doc):
    canvas.saveState()

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#666666"))

    canvas.drawString(
        18 * mm,
        10 * mm,
        "Nifty100 Financial Intelligence",
    )

    canvas.drawRightString(
        192 * mm,
        10 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


def build_sector_report(sector, sector_df, styles):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{safe_filename(sector)}_sector_report.pdf"
    output_path = OUTPUT_DIR / filename

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=15 * mm,
        title=f"{sector} Sector Report",
        author="Nifty100 Financial Intelligence",
    )

    medians = calculate_sector_medians(sector_df)
    best, worst = get_best_worst(sector_df)

    story = []

    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph(sector, styles["SectorTitle"]))
    story.append(
        Paragraph(
            f"Nifty100 Sector Report | {LATEST_YEAR} Financial Snapshot",
            styles["Subtitle"],
        )
    )

    summary_data = [
        ["Companies", str(len(sector_df))],
        ["Report Year", str(LATEST_YEAR)],
        ["Median Quality Score", fmt(medians["composite_quality_score"])],
    ]

    summary = Table(
        summary_data,
        colWidths=[65 * mm, 45 * mm],
    )

    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF0F6")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B7B7B7")),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story.append(summary)
    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph("Sector Median KPI Table", styles["SectionHeading"]))
    story.append(make_median_table(medians, styles))

    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph("Best & Worst Companies", styles["SectionHeading"]))
    story.append(make_best_worst_table(best, worst))

    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph("Company-Level KPI Comparison", styles["SectionHeading"]))
    story.append(make_company_table(sector_df))

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    return output_path


def generate_all_reports():
    df = load_sector_data()

    if len(df) != 92:
        raise ValueError(f"Expected 92 company records, found {len(df)}")

    styles = build_styles()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    generated = []

    for sector in sorted(df["broad_sector"].dropna().unique()):
        sector_df = df[df["broad_sector"] == sector].copy()

        output_path = build_sector_report(
            sector,
            sector_df,
            styles,
        )

        generated.append(output_path)

        print(
            f"[{len(generated)}/10] "
            f"{sector}: {output_path.stat().st_size:,} bytes"
        )

    return generated


if __name__ == "__main__":
    files = generate_all_reports()

    print()
    print(f"Generated {len(files)} sector reports.")
    print(f"Output directory: {OUTPUT_DIR}")
