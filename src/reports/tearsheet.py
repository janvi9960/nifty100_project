from pathlib import Path
import sqlite3
import os

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
    Image,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

DB_PATH = DATA_DIR / "nifty100.db"
PROS_CONS_PATH = OUTPUT_DIR / "pros_cons_generated.csv"
CASHFLOW_PATH = OUTPUT_DIR / "cashflow_intelligence.xlsx"
VALUATION_PATH = OUTPUT_DIR / "valuation_summary.xlsx"

TEARSHEET_DIR = REPORTS_DIR / "tearsheets"
RADAR_DIR = REPORTS_DIR / "radar_charts"


def load_data():
    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        "SELECT id, company_name FROM companies ORDER BY id",
        conn,
    )

    sectors = pd.read_sql_query(
        "SELECT * FROM sectors",
        conn,
    )

    pnl = pd.read_sql_query(
        "SELECT * FROM profitandloss ORDER BY company_id, year",
        conn,
    )

    ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios ORDER BY company_id, year",
        conn,
    )

    balance_sheet = pd.read_sql_query(
        "SELECT * FROM balancesheet ORDER BY company_id, year",
        conn,
    )

    cashflow = pd.read_sql_query(
        "SELECT * FROM cashflow ORDER BY company_id, year",
        conn,
    )

    conn.close()

    return {
        "companies": companies,
        "sectors": sectors,
        "pnl": pnl,
        "ratios": ratios,
        "balance_sheet": balance_sheet,
        "cashflow": cashflow,
        "pros_cons": pd.read_csv(PROS_CONS_PATH),
        "cashflow_intelligence": pd.read_excel(CASHFLOW_PATH),
        "valuation": pd.read_excel(VALUATION_PATH),
    }


def clean_company_name(name):
    return " ".join(str(name).split())


def find_radar(company_name):
    clean_name = clean_company_name(company_name)
    expected = RADAR_DIR / f"{clean_name}_radar.png"

    if expected.exists():
        return expected

    normalized_target = clean_name.lower()

    for path in RADAR_DIR.glob("*_radar.png"):
        normalized_file = clean_company_name(
            path.stem[:-6]
        ).lower()

        if normalized_file == normalized_target:
            return path

    return None


def fmt(value, decimals=2, suffix=""):
    if pd.isna(value):
        return "N/A"

    return f"{float(value):,.{decimals}f}{suffix}"


def latest_value(df, column):
    if df.empty or column not in df.columns:
        return None

    row = df.sort_values("year").iloc[-1]
    return row[column]


def get_sector(company_id, sectors):
    rows = sectors[sectors["company_id"] == company_id]

    if rows.empty:
        return "N/A"

    row = rows.iloc[0]

    for column in ["broad_sector", "sector_name", "sector", "name"]:
        if column in rows.columns and pd.notna(row[column]):
            return clean_company_name(row[column])

    return "N/A"


def build_styles():
    styles = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "TearsheetTitle",
            parent=styles["Title"],
            fontSize=20,
            leading=24,
            alignment=TA_LEFT,
            spaceAfter=4 * mm,
        ),
        "subtitle": ParagraphStyle(
            "TearsheetSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.grey,
            spaceAfter=5 * mm,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=styles["Heading2"],
            fontSize=12,
            leading=15,
            spaceBefore=3 * mm,
            spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=styles["BodyText"],
            fontSize=6.5,
            leading=7.5,
        ),
        "center": ParagraphStyle(
            "Center",
            parent=styles["BodyText"],
            fontSize=8,
            leading=10,
            alignment=TA_CENTER,
        ),
    }


def make_kpi_table(latest_pnl, latest_ratios):
    kpis = [
        ["Revenue", f"₹{fmt(latest_pnl.get('sales'))} Cr"],
        ["Net Profit", f"₹{fmt(latest_pnl.get('net_profit'))} Cr"],
        ["ROE", fmt(latest_ratios.get("return_on_equity"), suffix="%")],
        ["ROCE", fmt(latest_ratios.get("return_on_capital"), suffix="%")],
        ["D/E", fmt(latest_ratios.get("debt_to_equity"), decimals=3)],
        ["Quality Score", fmt(latest_ratios.get("composite_quality_score"))],
    ]

    table = Table(kpis, colWidths=[30 * mm] * 6)

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    return table



def create_revenue_profit_chart(pnl, company_id, asset_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    years = sorted(pnl["year"].dropna().unique())[-10:]
    df = pnl[pnl["year"].isin(years)].sort_values("year").copy()

    if df.empty:
        return None

    asset_dir.mkdir(parents=True, exist_ok=True)
    path = asset_dir / f"{company_id}_revenue_profit.png"

    x = np.arange(len(df))
    width = 0.38

    fig, ax = plt.subplots(figsize=(8.2, 2.7))
    ax.bar(x - width / 2, df["sales"], width, label="Revenue")
    ax.bar(x + width / 2, df["net_profit"], width, label="Net Profit")

    ax.set_title("10-Year Revenue & Net Profit")
    ax.set_xlabel("Year")
    ax.set_ylabel("? Cr")
    ax.set_xticks(x)
    ax.set_xticklabels([str(int(y)) for y in df["year"]], rotation=45)
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()

    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return path


def create_roe_roce_chart(ratios, company_id, asset_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    years = sorted(ratios["year"].dropna().unique())[-10:]
    df = ratios[ratios["year"].isin(years)].sort_values("year").copy()

    if df.empty:
        return None

    asset_dir.mkdir(parents=True, exist_ok=True)
    path = asset_dir / f"{company_id}_roe_roce.png"

    fig, ax = plt.subplots(figsize=(8.2, 2.5))

    ax.plot(
        df["year"],
        df["return_on_equity"],
        marker="o",
        label="ROE",
    )

    ax.plot(
        df["year"],
        df["return_on_capital"],
        marker="o",
        label="ROCE",
    )

    ax.set_title("ROE & ROCE Trend")
    ax.set_xlabel("Year")
    ax.set_ylabel("%")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()

    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return path


def create_balance_sheet_chart(balance_sheet, company_id, asset_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    years = sorted(balance_sheet["year"].dropna().unique())[-10:]
    df = balance_sheet[
        balance_sheet["year"].isin(years)
    ].sort_values("year").copy()

    if df.empty:
        return None

    components = pd.DataFrame(
        {
            "Borrowings": pd.to_numeric(df["borrowings"], errors="coerce").fillna(0),
            "Equity": pd.to_numeric(df["equity"], errors="coerce").fillna(0),
            "Reserves": pd.to_numeric(df["reserves"], errors="coerce").fillna(0),
        },
        index=df["year"],
    )

    components["Other Assets"] = (
        pd.to_numeric(df["total_assets"], errors="coerce").fillna(0)
        - components["Borrowings"]
        - components["Equity"]
        - components["Reserves"]
    ).clip(lower=0)

    asset_dir.mkdir(parents=True, exist_ok=True)
    path = asset_dir / f"{company_id}_balance_sheet.png"

    fig, ax = plt.subplots(figsize=(8.2, 2.7))

    bottom = None

    for column in components.columns:
        values = components[column].values

        if bottom is None:
            ax.bar(
                components.index.astype(str),
                values,
                label=column,
            )
            bottom = values.copy()
        else:
            ax.bar(
                components.index.astype(str),
                values,
                bottom=bottom,
                label=column,
            )
            bottom = bottom + values

    ax.set_title("Balance Sheet Composition")
    ax.set_xlabel("Year")
    ax.set_ylabel("? Cr")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(fontsize=7, ncol=4)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()

    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return path


def create_cashflow_waterfall(cashflow, company_id, asset_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    if cashflow.empty:
        return None

    latest = cashflow.sort_values("year").iloc[-1]

    labels = [
        "Opening",
        "Operating",
        "Investing",
        "Financing",
        "Net Cash",
    ]

    values = [
        0,
        float(latest["operating_activity"]),
        float(latest["investing_activity"]),
        float(latest["financing_activity"]),
        float(
            latest["operating_activity"]
            + latest["investing_activity"]
            + latest["financing_activity"]
        ),
    ]

    running = 0
    bottoms = []
    heights = []

    for index, value in enumerate(values):
        if index == 0:
            bottoms.append(0)
            heights.append(0)
        elif index == len(values) - 1:
            bottoms.append(0)
            heights.append(value)
        else:
            if value >= 0:
                bottoms.append(running)
                heights.append(value)
            else:
                bottoms.append(running + value)
                heights.append(abs(value))

            running += value

    asset_dir.mkdir(parents=True, exist_ok=True)
    path = asset_dir / f"{company_id}_cashflow_waterfall.png"

    fig, ax = plt.subplots(figsize=(8.2, 2.7))

    x = np.arange(len(labels))

    ax.bar(
        x,
        heights,
        bottom=bottoms,
        width=0.65,
    )

    ax.axhline(0, linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title(f"Cash Flow Waterfall ? {int(latest['year'])}")
    ax.set_ylabel("? Cr")
    ax.grid(axis="y", alpha=0.25)

    for i, value in enumerate(values):
        if i == 0:
            continue

        if i == len(values) - 1:
            y = value
        elif value >= 0:
            y = bottoms[i] + heights[i]
        else:
            y = bottoms[i]

        ax.text(
            i,
            y,
            f"{value:,.0f}",
            ha="center",
            va="bottom" if value >= 0 else "top",
            fontsize=7,
        )

    fig.tight_layout()

    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return path


def make_trend_table(pnl, ratios):
    years = sorted(set(pnl["year"]).intersection(set(ratios["year"])))[-10:]

    pnl10 = pnl[pnl["year"].isin(years)].set_index("year")
    ratios10 = ratios[ratios["year"].isin(years)].set_index("year")

    rows = [
        ["Year", "Revenue (₹ Cr)", "Net Profit (₹ Cr)", "ROE %", "ROCE %"]
    ]

    for year in years:
        rows.append(
            [
                str(year),
                fmt(pnl10.loc[year, "sales"], decimals=0),
                fmt(pnl10.loc[year, "net_profit"], decimals=0),
                fmt(ratios10.loc[year, "return_on_equity"]),
                fmt(ratios10.loc[year, "return_on_capital"]),
            ]
        )

    table = Table(
        rows,
        colWidths=[20 * mm, 35 * mm, 38 * mm, 25 * mm, 25 * mm],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.whitesmoke]),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ]
        )
    )

    return table


def make_balance_table(balance_sheet):
    latest = balance_sheet.sort_values("year").iloc[-1]

    rows = [
        ["Balance Sheet", "₹ Cr"],
        ["Borrowings", fmt(latest["borrowings"], 0)],
        ["Equity", fmt(latest["equity"], 0)],
        ["Reserves", fmt(latest["reserves"], 0)],
        ["Total Assets", fmt(latest["total_assets"], 0)],
    ]

    table = Table(rows, colWidths=[55 * mm, 35 * mm])

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    return table


def make_cashflow_table(cashflow):
    latest = cashflow.sort_values("year").iloc[-1]

    rows = [
        ["Cash Flow", "₹ Cr"],
        ["Operating Activity", fmt(latest["operating_activity"], 0)],
        ["Investing Activity", fmt(latest["investing_activity"], 0)],
        ["Financing Activity", fmt(latest["financing_activity"], 0)],
        [
            "Net Cash Flow",
            fmt(
                latest["operating_activity"]
                + latest["investing_activity"]
                + latest["financing_activity"],
                0,
            ),
        ],
    ]

    table = Table(rows, colWidths=[55 * mm, 35 * mm])

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("ALIGN", (1, 1), (1, -1), "RIGHT"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    return table


def make_intelligence_table(row):
    fields = [
        ("CFO Quality", "cfo_quality_label"),
        ("CapEx Intensity", "capex_label"),
        ("Capital Allocation", "capital_allocation_label"),
        ("Distress Flag", "distress_flag"),
        ("Deleveraging Flag", "deleveraging_flag"),
    ]

    rows = [["Cash Flow Intelligence", "Status"]]

    for label, column in fields:
        value = row.get(column, "N/A")

        if isinstance(value, bool):
            value = "Yes" if value else "No"

        rows.append([label, str(value)])

    table = Table(rows, colWidths=[55 * mm, 65 * mm])

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    return table


def make_valuation_table(row):
    columns = [
        ("P/E", "P/E"),
        ("P/B", "P/B"),
        ("EV/EBITDA", "EV/EBITDA"),
        ("FCF Yield", "FCF_yield_pct"),
        ("Valuation Flag", "flag"),
    ]

    rows = [["Valuation", "Value"]]

    for label, column in columns:
        value = row.get(column, "N/A")

        if column == "FCF_yield_pct" and pd.notna(value):
            value = f"{float(value):.2f}%"
        elif isinstance(value, float):
            value = f"{value:.2f}"

        rows.append([label, str(value)])

    table = Table(rows, colWidths=[55 * mm, 65 * mm])

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.darkgrey),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )

    return table


def make_pros_cons(data):
    rows = data.sort_values(
        ["sentiment", "confidence_score"],
        ascending=[True, False],
    )

    pros = rows[rows["sentiment"].astype(str).str.upper() == "PRO"].head(5)
    cons = rows[rows["sentiment"].astype(str).str.upper() == "CON"].head(5)

    left = [["PROS"]]
    for _, row in pros.iterrows():
        left.append(
            [
                Paragraph(
                    f"• {row['statement']}",
                    ParagraphStyle(
                        "Pros",
                        fontSize=6.5,
                        leading=7.5,
                    ),
                )
            ]
        )

    right = [["CONS"]]
    for _, row in cons.iterrows():
        right.append(
            [
                Paragraph(
                    f"• {row['statement']}",
                    ParagraphStyle(
                        "Cons",
                        fontSize=6.5,
                        leading=7.5,
                    ),
                )
            ]
        )

    max_len = max(len(left), len(right))

    while len(left) < max_len:
        left.append([""])

    while len(right) < max_len:
        right.append([""])

    combined = [
        [left[i][0], right[i][0]]
        for i in range(max_len)
    ]

    table = Table(combined, colWidths=[88 * mm, 88 * mm])

    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
            ]
        )
    )

    return table


def generate_tearsheet(company_id, data):
    companies = data["companies"]
    sectors = data["sectors"]
    pnl = data["pnl"]
    ratios = data["ratios"]
    balance_sheet = data["balance_sheet"]
    cashflow = data["cashflow"]
    pros_cons = data["pros_cons"]
    cashflow_intelligence = data["cashflow_intelligence"]
    valuation = data["valuation"]

    company_row = companies[companies["id"] == company_id].iloc[0]
    company_name = clean_company_name(company_row["company_name"])
    sector = get_sector(company_id, sectors)

    company_pnl = pnl[pnl["company_id"] == company_id].copy()
    company_ratios = ratios[ratios["company_id"] == company_id].copy()
    company_bs = balance_sheet[balance_sheet["company_id"] == company_id].copy()
    company_cf = cashflow[cashflow["company_id"] == company_id].copy()
    company_pros_cons = pros_cons[
        pros_cons["company_id"] == company_id
    ].copy()

    intelligence_rows = cashflow_intelligence[
        cashflow_intelligence["company_id"] == company_id
    ]

    valuation_rows = valuation[
        valuation["company_id"] == company_id
    ]

    intelligence = (
        intelligence_rows.iloc[0]
        if not intelligence_rows.empty
        else pd.Series(dtype=object)
    )

    valuation_row = (
        valuation_rows.iloc[0]
        if not valuation_rows.empty
        else pd.Series(dtype=object)
    )

    latest_pnl = (
        company_pnl.sort_values("year").iloc[-1]
        if not company_pnl.empty
        else pd.Series(dtype=float)
    )

    latest_ratios = (
        company_ratios.sort_values("year").iloc[-1]
        if not company_ratios.empty
        else pd.Series(dtype=float)
    )

    TEARSHEET_DIR.mkdir(parents=True, exist_ok=True)

    asset_dir = REPORTS_DIR / "tearsheet_assets"

    revenue_profit_chart = create_revenue_profit_chart(
        company_pnl,
        company_id,
        asset_dir,
    )

    roe_roce_chart = create_roe_roce_chart(
        company_ratios,
        company_id,
        asset_dir,
    )

    balance_sheet_chart = create_balance_sheet_chart(
        company_bs,
        company_id,
        asset_dir,
    )

    cashflow_waterfall = create_cashflow_waterfall(
        company_cf,
        company_id,
        asset_dir,
    )

    output_path = TEARSHEET_DIR / f"{company_id}_tearsheet.pdf"

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm,
    )

    styles = build_styles()
    story = []

    # PAGE 1
    story.append(Paragraph(company_name, styles["title"]))
    story.append(
        Paragraph(
            f"{company_id}  •  {sector}  •  Financial Tearsheet",
            styles["subtitle"],
        )
    )

    story.append(make_kpi_table(latest_pnl, latest_ratios))
    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("10-Year Revenue & Profit", styles["section"]))

    if revenue_profit_chart and revenue_profit_chart.exists():
        img = Image(str(revenue_profit_chart))
        img._restrictSize(175 * mm, 58 * mm)
        story.append(img)
    else:
        story.append(
            Paragraph(
                "Revenue and profit chart unavailable.",
                styles["body"],
            )
        )

    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph("ROE & ROCE Trend", styles["section"]))

    if roe_roce_chart and roe_roce_chart.exists():
        img = Image(str(roe_roce_chart))
        img._restrictSize(175 * mm, 53 * mm)
        story.append(img)
    else:
        story.append(
            Paragraph(
                "ROE/ROCE chart unavailable.",
                styles["body"],
            )
        )

    # PAGE 2
    story.append(PageBreak())

    story.append(
        Paragraph(
            f"{company_id} — Balance Sheet & Cash Flow Intelligence",
            styles["section"],
        )
    )

    story.append(Paragraph("Balance Sheet Composition", styles["section"]))

    if balance_sheet_chart and balance_sheet_chart.exists():
        img = Image(str(balance_sheet_chart))
        img._restrictSize(175 * mm, 48 * mm)
        story.append(img)
    else:
        story.append(
            Paragraph(
                "Balance sheet chart unavailable.",
                styles["body"],
            )
        )

    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("Cash Flow Waterfall", styles["section"]))

    if cashflow_waterfall and cashflow_waterfall.exists():
        img = Image(str(cashflow_waterfall))
        img._restrictSize(175 * mm, 48 * mm)
        story.append(img)
    else:
        story.append(
            Paragraph(
                "Cash flow waterfall unavailable.",
                styles["body"],
            )
        )

    story.append(Spacer(1, 3 * mm))

    story.append(Paragraph("Capital Allocation & Cash Flow Intelligence", styles["section"]))
    story.append(make_intelligence_table(intelligence))
    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("Pros & Cons", styles["section"]))
    story.append(make_pros_cons(company_pros_cons))
    story.append(Spacer(1, 2 * mm))

    story.append(Paragraph("Valuation Snapshot", styles["section"]))
    story.append(make_valuation_table(valuation_row))

    doc.build(story)

    return output_path


def main():
    print("Loading Sprint 5 tearsheet data...")
    data = load_data()

    companies = data["companies"]["id"].tolist()

    print(f"Generating tearsheets for {len(companies)} companies...")

    success = 0
    failed = []

    for index, company_id in enumerate(companies, start=1):
        try:
            output = generate_tearsheet(company_id, data)
            size = output.stat().st_size

            print(
                f"[{index}/{len(companies)}] "
                f"{company_id}: {size:,} bytes"
            )

            success += 1

        except Exception as exc:
            print(f"[{index}/{len(companies)}] {company_id}: FAILED - {exc}")
            failed.append((company_id, str(exc)))

    print()
    print("=== TEARSHEET GENERATION SUMMARY ===")
    print(f"Total companies: {len(companies)}")
    print(f"Successful: {success}")
    print(f"Failed: {len(failed)}")

    if failed:
        print()
        print("Failed companies:")
        for company_id, error in failed:
            print(f"  {company_id}: {error}")


if __name__ == "__main__":
    main()




