from pathlib import Path
import sqlite3
import re
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, KeepTogether
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
RADAR_DIR = PROJECT_ROOT / "reports" / "radar_charts"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "peer_group"
OUTPUT_FILE = OUTPUT_DIR / "Nifty100_Peer_Group_Report.pdf"

METRICS = [
    "ROE",
    "ROCE",
    "NPM",
    "D/E",
    "FCF",
    "PAT CAGR 5yr",
    "Revenue CAGR 5yr",
    "EPS CAGR 5yr",
    "Interest Coverage",
    "Asset Turnover",
]

METRIC_LABELS = {
    "ROE": "ROE %",
    "ROCE": "ROCE %",
    "NPM": "NPM %",
    "D/E": "D/E",
    "FCF": "FCF",
    "PAT CAGR 5yr": "PAT CAGR 5yr %",
    "Revenue CAGR 5yr": "Revenue CAGR 5yr %",
    "EPS CAGR 5yr": "EPS CAGR 5yr %",
    "Interest Coverage": "Interest Coverage",
    "Asset Turnover": "Asset Turnover",
}


def clean_name(value):
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def radar_path(company_name):
    cleaned = clean_name(company_name)
    exact = RADAR_DIR / f"{cleaned}_radar.png"
    if exact.exists():
        return exact

    normalized = re.sub(r"\s+", " ", cleaned).strip().lower()

    for path in RADAR_DIR.glob("*_radar.png"):
        candidate = clean_name(path.stem[:-6])
        if candidate.lower() == normalized:
            return path

    return None


def format_value(metric, value):
    if pd.isna(value):
        return "N/A"

    if metric == "FCF":
        return f"{float(value):,.0f}"

    if metric == "D/E":
        return f"{float(value):.2f}"

    if metric in {"ROE", "ROCE", "NPM", "PAT CAGR 5yr",
                  "Revenue CAGR 5yr", "EPS CAGR 5yr"}:
        return f"{float(value):.2f}%"

    return f"{float(value):.2f}"


def load_data():
    conn = sqlite3.connect(DB_PATH)

    peer_groups = pd.read_sql_query(
        """
        SELECT
            pg.peer_group_name,
            pg.company_id,
            pg.is_benchmark,
            c.company_name
        FROM peer_groups pg
        JOIN companies c
            ON c.id = pg.company_id
        ORDER BY pg.peer_group_name, pg.is_benchmark DESC, pg.company_id
        """,
        conn,
    )

    percentiles = pd.read_sql_query(
        """
        SELECT
            company_id,
            peer_group_name,
            metric,
            value,
            percentile_rank,
            year
        FROM peer_percentiles
        WHERE year = (
            SELECT MAX(year)
            FROM peer_percentiles
        )
        """,
        conn,
    )

    conn.close()

    if peer_groups.empty:
        raise RuntimeError("peer_groups table is empty.")

    if percentiles.empty:
        raise RuntimeError("peer_percentiles table is empty.")

    return peer_groups, percentiles


def build_styles():
    styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "PeerTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "PeerSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.grey,
            spaceAfter=12,
        ),
        "heading": ParagraphStyle(
            "PeerHeading",
            parent=styles["Heading1"],
            fontSize=15,
            leading=18,
            spaceBefore=4,
            spaceAfter=7,
        ),
        "subheading": ParagraphStyle(
            "PeerSubheading",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            spaceBefore=5,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "PeerBody",
            parent=styles["BodyText"],
            fontSize=8.5,
            leading=11,
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "PeerSmall",
            parent=styles["BodyText"],
            fontSize=7,
            leading=8.5,
        ),
        "table": ParagraphStyle(
            "PeerTable",
            parent=styles["BodyText"],
            fontSize=6.5,
            leading=7.5,
        ),
    }


def make_table(data, widths, header=True, font_size=6.5):
    table = Table(
        data,
        colWidths=widths,
        repeatRows=1 if header else 0,
        hAlign="LEFT",
    )

    commands = [
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8B8B8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]

    if header:
        commands.extend([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ])

    table.setStyle(TableStyle(commands))
    return table


def build_overview(peer_groups, percentiles, styles):
    story = []

    story.append(Paragraph(
        "Nifty100 Peer Group Intelligence Report",
        styles["title"]
    ))

    story.append(Paragraph(
        "Peer benchmarking using 2024 financial metrics and percentile rankings",
        styles["subtitle"]
    ))

    group_summary = (
        peer_groups.groupby("peer_group_name")
        .agg(
            Companies=("company_id", "nunique"),
            Benchmark=("is_benchmark", "sum")
        )
        .reset_index()
        .sort_values("peer_group_name")
    )

    overview = [["Peer Group", "Companies", "Benchmark"]]

    for _, row in group_summary.iterrows():
        overview.append([
            row["peer_group_name"],
            str(int(row["Companies"])),
            str(int(row["Benchmark"])),
        ])

    story.append(Paragraph("Peer Group Coverage", styles["heading"]))

    story.append(make_table(
        overview,
        [90 * mm, 35 * mm, 35 * mm],
    ))

    story.append(Spacer(1, 8))

    story.append(Paragraph(
        f"Total peer groups: {peer_groups.peer_group_name.nunique()} | "
        f"Total companies: {peer_groups.company_id.nunique()} | "
        f"Peer metric records: {len(percentiles)} | "
        f"Report year: {int(percentiles.year.max())}",
        styles["body"]
    ))

    story.append(Paragraph(
        "Percentile ranks are calculated within each peer group. "
        "Higher percentile generally indicates stronger relative positioning "
        "for that metric; D/E should be interpreted as a leverage metric. "
        "Missing source values are shown as N/A.",
        styles["body"]
    ))

    story.append(PageBreak())

    return story


def build_group_section(group_name, group_df, pct_df, styles):
    story = []

    group_df = group_df.sort_values(
        ["is_benchmark", "company_id"],
        ascending=[False, True]
    )

    benchmark_rows = group_df[group_df["is_benchmark"] == 1]
    benchmark = (
        benchmark_rows.iloc[0]["company_id"]
        if not benchmark_rows.empty
        else "N/A"
    )

    story.append(Paragraph(
        f"{group_name}",
        styles["heading"]
    ))

    story.append(Paragraph(
        f"Companies: {len(group_df)} &nbsp;&nbsp; "
        f"Benchmark: <b>{benchmark}</b> &nbsp;&nbsp; "
        f"Year: 2024",
        styles["body"]
    ))

    # Company comparison table
    wide_header = [
        "Ticker",
        "Company",
        "Bench.",
    ] + [METRIC_LABELS[m] for m in METRICS]

    rows = [wide_header]

    for _, company in group_df.iterrows():
        company_id = company["company_id"]

        subset = pct_df[
            (pct_df["company_id"] == company_id)
            & (pct_df["peer_group_name"] == group_name)
        ]

        values = []
        for metric in METRICS:
            match = subset[subset["metric"] == metric]
            value = match.iloc[0]["value"] if not match.empty else float("nan")
            values.append(format_value(metric, value))

        rows.append([
            company_id,
            clean_name(company["company_name"]),
            "YES" if int(company["is_benchmark"]) == 1 else "",
            *values,
        ])

    widths = [
        19 * mm,
        42 * mm,
        14 * mm,
        17 * mm,
        17 * mm,
        17 * mm,
        14 * mm,
        20 * mm,
        21 * mm,
        23 * mm,
        21 * mm,
        21 * mm,
        19 * mm,
    ]

    # Keep the table within landscape A4 usable width.
    widths = [w * 0.88 for w in widths]

    table = Table(
        rows,
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B8B8B8")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 5.3),
        ("LEADING", (0, 0), (-1, -1), 6.2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))

    story.append(Paragraph(
        "KPI Comparison",
        styles["subheading"]
    ))
    story.append(table)
    story.append(Spacer(1, 8))

    # Percentile table
    percentile_header = ["Ticker"] + [
        METRIC_LABELS[m] for m in METRICS
    ]

    percentile_rows = [percentile_header]

    for _, company in group_df.iterrows():
        company_id = company["company_id"]

        subset = pct_df[
            (pct_df["company_id"] == company_id)
            & (pct_df["peer_group_name"] == group_name)
        ]

        row = [company_id]

        for metric in METRICS:
            match = subset[subset["metric"] == metric]
            if match.empty or pd.isna(match.iloc[0]["percentile_rank"]):
                row.append("N/A")
            else:
                row.append(f"{float(match.iloc[0]['percentile_rank']):.0f}")

        percentile_rows.append(row)

    percentile_widths = [20 * mm] + [23 * mm] * len(METRICS)
    percentile_widths = [w * 0.88 for w in percentile_widths]

    percentile_table = Table(
        percentile_rows,
        colWidths=percentile_widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    percentile_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B8B8B8")),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8E8E8")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 5.5),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 1), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
    ]))

    story.append(Paragraph(
        "Peer Percentile Ranks",
        styles["subheading"]
    ))
    story.append(percentile_table)
    story.append(Spacer(1, 7))

    # Radar charts: benchmark + peers
    story.append(Paragraph(
        "Peer Radar Charts",
        styles["subheading"]
    ))

    radar_items = []

    for _, company in group_df.iterrows():
        path = radar_path(company["company_name"])
        if path:
            img = Image(str(path))
            img.drawWidth = 47 * mm
            img.drawHeight = 47 * mm

            label = Paragraph(
                f"<b>{company['company_id']}</b><br/>{clean_name(company['company_name'])}",
                styles["small"]
            )

            radar_items.append([img, label])

    if radar_items:
        radar_table = Table(
            radar_items,
            colWidths=[52 * mm, 42 * mm],
            hAlign="LEFT",
        )
        radar_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))

        # Arrange radar entries in pairs across the page.
        paired = []
        for i in range(0, len(radar_items), 2):
            left = radar_items[i]
            right = radar_items[i + 1] if i + 1 < len(radar_items) else ["", ""]
            paired.append(left + right)

        radar_grid = Table(
            paired,
            colWidths=[48 * mm, 43 * mm, 48 * mm, 43 * mm],
            hAlign="LEFT",
        )

        radar_grid.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 2),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))

        story.append(radar_grid)
    else:
        story.append(Paragraph(
            "No radar images were available for this peer group.",
            styles["body"]
        ))

    story.append(Paragraph(
        "Interpretation note: percentile ranks are peer-relative and should "
        "be read together with the underlying KPI values. Higher ROE, ROCE, "
        "NPM, growth, FCF, interest coverage and asset turnover are generally "
        "favorable; lower D/E generally indicates lower leverage.",
        styles["small"]
    ))

    return story


def build_report():
    peer_groups, percentiles = load_data()

    if peer_groups.peer_group_name.nunique() != 11:
        raise RuntimeError(
            f"Expected 11 peer groups, found "
            f"{peer_groups.peer_group_name.nunique()}."
        )

    if peer_groups.company_id.nunique() != 56:
        raise RuntimeError(
            f"Expected 56 peer companies, found "
            f"{peer_groups.company_id.nunique()}."
        )

    styles = build_styles()

    doc = SimpleDocTemplate(
        str(OUTPUT_FILE),
        pagesize=landscape(A4),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
        title="Nifty100 Peer Group Intelligence Report",
        author="Nifty100 Project",
    )

    story = build_overview(peer_groups, percentiles, styles)

    groups = sorted(peer_groups.peer_group_name.unique())

    for index, group_name in enumerate(groups):
        group_df = peer_groups[
            peer_groups.peer_group_name == group_name
        ].copy()

        pct_df = percentiles[
            percentiles.peer_group_name == group_name
        ].copy()

        story.extend(
            build_group_section(
                group_name,
                group_df,
                pct_df,
                styles,
            )
        )

        if index < len(groups) - 1:
            story.append(PageBreak())

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    doc.build(story)

    print(f"Generated: {OUTPUT_FILE}")
    print(f"Size: {OUTPUT_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    build_report()
