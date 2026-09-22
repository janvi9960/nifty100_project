from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "docs"
DOCS.mkdir(parents=True, exist_ok=True)


# -----------------------------
# Styles
# -----------------------------
styles = getSampleStyleSheet()

styles.add(
    ParagraphStyle(
        name="TitleCustom",
        parent=styles["Title"],
        fontSize=22,
        leading=27,
        alignment=TA_CENTER,
        spaceAfter=12,
    )
)

styles.add(
    ParagraphStyle(
        name="H1Custom",
        parent=styles["Heading1"],
        fontSize=16,
        leading=20,
        spaceBefore=8,
        spaceAfter=8,
    )
)

styles.add(
    ParagraphStyle(
        name="H2Custom",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=6,
        spaceAfter=5,
    )
)

styles.add(
    ParagraphStyle(
        name="BodyCustom",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        spaceAfter=6,
    )
)

styles.add(
    ParagraphStyle(
        name="SmallCustom",
        parent=styles["BodyText"],
        fontSize=8,
        leading=10,
    )
)


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)

    canvas.drawString(
        18 * mm,
        10 * mm,
        "Nifty100 Analytics Project — Analyst Guide",
    )

    canvas.drawRightString(
        192 * mm,
        10 * mm,
        f"Page {doc.page}",
    )

    canvas.restoreState()


def bullet(text):
    return Paragraph("• " + text, styles["BodyCustom"])


# =========================================================
# ANALYST GUIDE
# =========================================================

def make_guide():

    path = DOCS / "analyst_guide.pdf"

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=17 * mm,
        bottomMargin=17 * mm,
    )

    story = []

    # Page 1
    story += [
        Paragraph(
            "Nifty100 Analytics Platform",
            styles["TitleCustom"],
        ),

        Paragraph(
            "Analyst Guide",
            styles["H1Custom"],
        ),

        Spacer(1, 8),

        Paragraph(
            "A practical guide for exploring the Nifty100 analytics dashboard, "
            "screening companies, comparing peers, reviewing financial trends, "
            "understanding capital allocation, and accessing generated reports.",
            styles["BodyCustom"],
        ),

        Spacer(1, 10),

        Paragraph(
            "Project Scope",
            styles["H2Custom"],
        ),

        bullet(
            "Coverage: 92 Nifty100 companies represented in the project dataset."
        ),

        bullet(
            "Dashboard contains 8 screens: Home, Profile, Screener, Peers, "
            "Trends, Sectors, Capital, and Reports."
        ),

        bullet(
            "Analytics include financial ratios, screening presets, peer "
            "comparison, valuation signals, cash-flow intelligence, "
            "pros/cons, clustering, and generated reports."
        ),

        bullet(
            "API layer provides programmatic access to company, financial, "
            "screening, peer, valuation, sector, portfolio, and document information."
        ),

        Spacer(1, 8),

        Paragraph(
            "How to Use This Guide",
            styles["H2Custom"],
        ),

        Paragraph(
            "Start with Home for navigation and high-level context. "
            "Use Profile for an individual company, Screener for filtering, "
            "Peers for comparison, Trends and Sectors for broader analysis, "
            "Capital for cash-flow and allocation intelligence, and Reports "
            "for generated documents.",
            styles["BodyCustom"],
        ),

        PageBreak(),
    ]

    # Page 2
    story += [
        Paragraph(
            "1. Platform Overview",
            styles["H1Custom"],
        ),

        Paragraph(
            "Typical Analyst Workflow",
            styles["H2Custom"],
        ),

        bullet("1) Select a company or screening objective."),
        bullet("2) Review core financial and operating metrics."),
        bullet("3) Compare the company with peers and sector context."),
        bullet("4) Review trends and capital-allocation signals."),
        bullet("5) Review valuation and qualitative intelligence."),
        bullet("6) Open the relevant tear sheet or sector report."),

        Paragraph(
            "Key Analytical Outputs",
            styles["H2Custom"],
        ),
    ]

    data = [
        ["Output", "Purpose"],
        ["Financial ratios", "Profitability, leverage, valuation and efficiency measures."],
        ["Screener", "Rule/preset-based company filtering."],
        ["Peer comparison", "Compare companies within peer groups."],
        ["Valuation summary", "Valuation metrics and valuation flags."],
        ["Cash-flow intelligence", "CFO quality, CapEx and capital-allocation interpretation."],
        ["Pros/cons", "Generated company-level qualitative insights."],
        ["Cluster labels", "Five data-driven company archetypes."],
        ["Tear sheets / sector reports", "Shareable company and sector summaries."],
    ]

    table = Table(
        data,
        colWidths=[45 * mm, 125 * mm],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("LEADING", (0, 0), (-1, -1), 11),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )

    story += [
        table,
        PageBreak(),
    ]

    # Dashboard screens
    screens = [
        (
            "2. Home Screen",
            [
                "Use Home as the entry point to the dashboard.",
                "Review the available analysis areas and navigation.",
                "Confirm the dashboard is connected to the project database.",
                "Use the navigation controls to move between analytical screens.",
            ],
        ),

        (
            "3. Profile Screen",
            [
                "Use Profile for a company-level view of an individual Nifty100 company.",
                "Review company identity, financial indicators, valuation information and qualitative insights.",
                "Use the profile as the starting point for a deeper company review.",
                "If a field is blank, distinguish unavailable data from a true zero value.",
            ],
        ),

        (
            "4. Screener Screen",
            [
                "Use Screener to narrow the 92-company universe using financial metrics and predefined logic.",
                "Project presets include Quality Compounder, Value Pick, Growth Accelerator, Dividend Champion, Debt-Free Blue Chip, and Turnaround Watch.",
                "Review the selected metrics together with the resulting companies.",
                "Use the export functionality when a filtered company list is required.",
            ],
        ),

        (
            "5. Peers Screen",
            [
                "Use Peers to compare a company with its peer group.",
                "Review profitability, growth, leverage and other available metrics.",
                "Sector and peer context can help explain differences between companies.",
                "Use peer results together with Screener and Trends.",
            ],
        ),

        (
            "6. Trends Screen",
            [
                "Use Trends to examine historical movement in financial and operating metrics.",
                "Look for direction, consistency, inflection points and unusual changes.",
                "Historical data should be interpreted across multiple periods where available.",
                "Cross-check unusual values against the underlying data.",
            ],
        ),

        (
            "7. Sectors Screen",
            [
                "Use Sectors to understand company and metric patterns at sector level.",
                "Compare sector medians and individual company values.",
                "Sector context is useful for valuation and peer interpretation.",
                "Use sector reports for documented sector-level analysis.",
            ],
        ),

        (
            "8. Capital Screen",
            [
                "Use Capital for cash-flow quality, CapEx and capital-allocation intelligence.",
                "Project classifications include Shareholder Returns, Reinvestor, Mixed, Growth Funded by Debt, and Liquidating Assets.",
                "A separate distress condition is used for negative CFO combined with positive CFF.",
                "Treat classifications as analytical signals derived from project rules and data.",
            ],
        ),

        (
            "9. Reports Screen",
            [
                "Use Reports to access generated company tear sheets and sector reports.",
                "Tear sheets provide compact company summaries.",
                "Sector reports provide broader analytical summaries.",
                "Check that the expected report file exists before distribution.",
            ],
        ),
    ]

    for title, bullets in screens:

        story.append(
            Paragraph(
                title,
                styles["H1Custom"],
            )
        )

        for item in bullets:
            story.append(bullet(item))

        story.append(Spacer(1, 5))
        story.append(PageBreak())

    # Page 11
    story += [
        Paragraph(
            "10. Valuation & Intelligence Outputs",
            styles["H1Custom"],
        ),

        Paragraph(
            "Valuation Summary",
            styles["H2Custom"],
        ),

        bullet(
            "The valuation output contains 92 company rows."
        ),

        bullet(
            "Core fields include P/E, P/B, EV/EBITDA, FCF yield, "
            "five-year median P/E and comparison with sector median P/E."
        ),

        bullet(
            "Project valuation flags include Fair, Discount and Caution."
        ),

        bullet(
            "Review the underlying metrics before interpreting a valuation flag."
        ),

        Paragraph(
            "Qualitative Intelligence",
            styles["H2Custom"],
        ),

        bullet(
            "Pros/cons generation covers all 92 companies with at least one positive and one negative insight."
        ),

        bullet(
            "Cash-flow intelligence combines CFO, CapEx and financing information into analyst-friendly classifications."
        ),

        bullet(
            "Cluster analysis groups the 92 companies into five project-defined archetypes using standardized financial features."
        ),

        PageBreak(),
    ]

    # Page 12
    story += [
        Paragraph(
            "11. API, QA & Troubleshooting",
            styles["H1Custom"],
        ),

        Paragraph(
            "API",
            styles["H2Custom"],
        ),

        bullet(
            "The FastAPI layer exposes company, financial statement, ratio, tear-sheet, screener, sector, peer, valuation, market-cap, portfolio-statistics and document endpoints."
        ),

        bullet(
            "OpenAPI documentation can be used to inspect available paths and response structures."
        ),

        Paragraph(
            "Quality Assurance",
            styles["H2Custom"],
        ),

        bullet(
            "The latest recorded full test run completed with 147 passed tests and 1 warning."
        ),

        bullet(
            "Automated tests cover API, ETL and KPI functionality."
        ),

        bullet(
            "After changing analytical logic, rerun relevant tests and then the full test suite."
        ),

        Paragraph(
            "Common Troubleshooting",
            styles["H2Custom"],
        ),

        bullet(
            "If the dashboard does not load, confirm the virtual environment is active and Streamlit starts without errors."
        ),

        bullet(
            "If data is missing, verify the active database path and expected output files."
        ),

        bullet(
            "If a PDF or CSV is missing, check the docs/output folders and rerun the relevant generation step."
        ),

        bullet(
            "When using PowerShell, type only the command and do not copy the PowerShell prompt."
        ),

        Paragraph(
            "Quick Reference",
            styles["H2Custom"],
        ),

        bullet(
            "Dashboard: Home → Profile → Screener → Peers → Trends → Sectors → Capital → Reports."
        ),

        bullet(
            "Database: data/nifty100.db"
        ),

        bullet(
            "Generated outputs: output/"
        ),

        bullet(
            "Documentation: docs/"
        ),

        bullet(
            "Testing: pytest"
        ),
    ]

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    return path


# =========================================================
# ACCEPTANCE CHECKLIST
# =========================================================

def make_checklist():

    path = DOCS / "acceptance_checklist.pdf"

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=17 * mm,
    )

    story = [
        Paragraph(
            "Nifty100 Analytics Project",
            styles["TitleCustom"],
        ),

        Paragraph(
            "Acceptance Checklist — Sprint 6",
            styles["H1Custom"],
        ),

        Paragraph(
            "Checklist for final verification of Sprint 6 deliverables and acceptance criteria.",
            styles["BodyCustom"],
        ),
    ]

    items = [
        ("AC-01", "Database and core data", "Verified", "Nifty100 database available and populated."),
        ("AC-02", "Load audit", "Verified", "Load-audit output generated."),
        ("AC-03", "Exploratory SQL", "Verified", "Exploratory SQL analysis completed."),
        ("AC-04", "Financial ratios", "Verified", "Financial-ratio output generated."),
        ("AC-05", "Capital allocation", "Verified", "Capital-allocation output generated."),
        ("AC-06", "Screener", "Verified", "Screener presets and output available."),
        ("AC-07", "Peer comparison", "Verified", "Peer groups and comparison output available."),
        ("AC-08", "Radar charts", "Verified", "Radar-chart output available."),
        ("AC-09", "Dashboard", "Verified", "8-screen Streamlit dashboard available."),
        ("AC-10", "Valuation summary", "Verified", "Valuation summary generated for 92 companies."),
        ("AC-11", "Cash-flow intelligence", "Verified", "Cash-flow intelligence output generated."),
        ("AC-12", "Pros/cons", "Verified", "Pros/cons generated for 92 companies."),
        ("AC-13", "Parsed analysis", "Verified", "Analysis parsing output generated."),
        ("AC-14", "Tear sheets", "Verified", "Company tear sheets generated."),
        ("AC-15", "Sector reports", "Verified", "Sector-level reports generated."),
        ("AC-16", "Portfolio statistics", "Verified", "Portfolio statistics output available."),
        ("AC-17", "Cluster labels", "Verified", "92 companies clustered into 5 archetypes."),
        ("AC-18", "FastAPI", "Verified", "API application and endpoint collection available."),
        ("AC-19", "Automated tests", "Verified", "Latest full test run: 147 passed, 1 warning."),
        ("AC-20", "Analyst guide", "Verified", "Analyst guide generated as a multi-page PDF."),
        ("AC-21", "Acceptance checklist", "Verified", "Acceptance checklist generated."),
        ("AC-22", "Validation failures", "To Verify", "Confirm output/validation_failures.csv exists with company_id, field, issue, severity."),
        ("AC-23", "Final repository status", "To Verify", "Confirm all intended files are committed and git status is clean."),
    ]

    data = [
        ["ID", "Area", "Status", "Acceptance Evidence"]
    ]

    data.extend(items)

    table = Table(
        data,
        colWidths=[
            18 * mm,
            42 * mm,
            27 * mm,
            93 * mm,
        ],
        repeatRows=1,
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.3),
                ("LEADING", (0, 0), (-1, -1), 9.2),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )

    story += [
        table,
        Spacer(1, 8),
        Paragraph(
            "Final note: AC-22 and AC-23 must be checked from the local project before final sign-off.",
            styles["SmallCustom"],
        ),
    ]

    doc.build(
        story,
        onFirstPage=footer,
        onLaterPages=footer,
    )

    return path


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    guide = make_guide()
    checklist = make_checklist()

    print()
    print("======================================")
    print("Nifty100 PDF Generation Complete")
    print("======================================")
    print(f"Created: {guide}")
    print(f"Created: {checklist}")
    print()