from pathlib import Path
import sqlite3
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
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
OUTPUT_DIR = PROJECT_ROOT / "reports" / "portfolio"
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


def load_portfolio_data():
    query = """
        SELECT
            fr.company_id,
            c.company_name,
            s.broad_sector AS sector,
            fr.year,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            fr.return_on_equity,
            fr.return_on_capital,
            fr.net_profit_margin,
            fr.debt_to_equity,
            fr.interest_coverage,
            fr.composite_quality_score
        FROM financial_ratios fr
        JOIN companies c
            ON c.id = fr.company_id
        LEFT JOIN sectors s
            ON s.company_id = fr.company_id
        WHERE fr.year = ?
        ORDER BY fr.composite_quality_score DESC
    """

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(query, conn, params=[LATEST_YEAR])

    if df.empty:
        raise ValueError("No portfolio data found.")

    return df


def fmt(value, suffix=""):
    if pd.isna(value):
        return "N/A"
    return f"{float(value):.2f}{suffix}"


def clean_name(value):
    return str(value).replace("\n", " ").strip()


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="PortfolioTitle",
            parent=styles["Title"],
            fontSize=17,
            leading=20,
            alignment=TA_CENTER,
            spaceAfter=5,
        )
    )

    styles.add(
        ParagraphStyle(
            name="PortfolioSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#555555"),
            spaceAfter=8,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            fontSize=10,
            leading=12,
            spaceBefore=5,
            spaceAfter=4,
        )
    )

    styles.add(
        ParagraphStyle(
            name="Small",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=9,
        )
    )

    return styles


def make_identity_table(row, styles):
    data = [
        [
            Paragraph("<b>Ticker</b>", styles["Small"]),
            Paragraph(str(row["company_id"]), styles["Small"]),
            Paragraph("<b>Sector</b>", styles["Small"]),
            Paragraph(clean_name(row["sector"]), styles["Small"]),
        ],
        [
            Paragraph("<b>Company</b>", styles["Small"]),
            Paragraph(clean_name(row["company_name"]), styles["Small"]),
            Paragraph("<b>Report Year</b>", styles["Small"]),
            Paragraph(str(int(row["year"])), styles["Small"]),
        ],
    ]

    table = Table(data, colWidths=[22 * mm, 58 * mm, 25 * mm, 75 * mm])

    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eeeeee")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#eeeeee")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    return table


def make_kpi_table(row, styles):
    data = [
        [
            Paragraph("<b>KPI</b>", styles["Small"]),
            Paragraph("<b>Company</b>", styles["Small"]),
        ]
    ]

    for column in KPI_COLUMNS:
        suffix = "%" if column not in {"debt_to_equity", "interest_coverage", "composite_quality_score"} else ""
        data.append(
            [
                Paragraph(KPI_LABELS[column], styles["Small"]),
                Paragraph(fmt(row[column], suffix), styles["Small"]),
            ]
        )

    table = Table(data, colWidths=[100 * mm, 35 * mm], hAlign="LEFT")

    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eeeeee")),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
            ]
        )
    )

    return table


def make_rank_table(df, row, styles):
    quality = row["composite_quality_score"]

    if pd.isna(quality):
        rank = "N/A"
    else:
        ranked = df["composite_quality_score"].rank(
            ascending=False, method="min", na_option="bottom"
        )
        rank = int(ranked[df.index[df["company_id"] == row["company_id"]][0]])

    valid_scores = df["composite_quality_score"].dropna()

    if pd.isna(quality) or valid_scores.empty:
        percentile = "N/A"
    else:
        percentile_value = (valid_scores <= float(quality)).mean() * 100
        percentile = f"{percentile_value:.1f}%"

    data = [
        [
            Paragraph("<b>Portfolio Rank</b>", styles["Small"]),
            Paragraph(f"{rank} / {len(df)}", styles["Small"]),
        ],
        [
            Paragraph("<b>Quality Score</b>", styles["Small"]),
            Paragraph(fmt(quality), styles["Small"]),
        ],
        [
            Paragraph("<b>Score Percentile</b>", styles["Small"]),
            Paragraph(percentile, styles["Small"]),
        ],
    ]

    table = Table(data, colWidths=[45 * mm, 45 * mm], hAlign="LEFT")

    table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eeeeee")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )

    return table


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.grey)
    canvas.drawCentredString(
        A4[0] / 2,
        8 * mm,
        f"Nifty100 Portfolio Summary | Page {doc.page}",
    )
    canvas.restoreState()


def build_company_report(df, row):
    ticker = str(row["company_id"])
    output_path = OUTPUT_DIR / f"{ticker}_portfolio_summary.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=12 * mm,
        bottomMargin=14 * mm,
    )

    styles = build_styles()

    story = []

    story.append(Paragraph("Nifty100 Portfolio Summary", styles["PortfolioTitle"]))
    story.append(
        Paragraph(
            f"{clean_name(row['company_name'])} | 2024 Financial Snapshot",
            styles["PortfolioSubtitle"],
        )
    )

    story.append(make_identity_table(row, styles))
    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Portfolio Position", styles["Section"]))

    rank_table = make_rank_table(df, row, styles)
    story.append(rank_table)

    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Key Financial KPIs", styles["Section"]))
    story.append(make_kpi_table(row, styles))

    story.append(Spacer(1, 5 * mm))

    story.append(Paragraph("Portfolio Context", styles["Section"]))

    sector = clean_name(row["sector"])
    quality = fmt(row["composite_quality_score"])

    context_text = (
        f"This portfolio summary places <b>{clean_name(row['company_name'])}</b> "
        f"({ticker}) within the Nifty100 universe for the {LATEST_YEAR} reporting year. "
        f"The company belongs to the <b>{sector}</b> sector and has a composite "
        f"quality score of <b>{quality}</b>. The ranking and percentile are calculated "
        f"against the {len(df)} companies represented in the 2024 financial-ratio dataset."
    )

    story.append(Paragraph(context_text, styles["Small"]))

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    return output_path


def generate_all_reports():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = load_portfolio_data()

    if len(df) != 92:
        raise ValueError(
            f"Expected 92 companies for portfolio report, found {len(df)}."
        )

    generated = []

    for index, (_, row) in enumerate(df.iterrows(), start=1):
        output_path = build_company_report(df, row)
        generated.append(output_path)

        print(
            f"[{index}/{len(df)}] "
            f"{row['company_id']}: {output_path.stat().st_size:,} bytes"
        )

    return generated


if __name__ == "__main__":
    files = generate_all_reports()

    print()
    print(f"Generated {len(files)} portfolio reports.")
    print(f"Output directory: {OUTPUT_DIR}")
