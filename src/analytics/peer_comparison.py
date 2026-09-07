from pathlib import Path
import sqlite3

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment
from openpyxl.utils import get_column_letter


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
OUTPUT_FILE = PROJECT_ROOT / "output" / "peer_comparison.xlsx"


# ============================================================
# CONFIGURATION
# ============================================================

PERCENTILE_METRICS = [
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


METRIC_COLUMNS = [
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
    "Revenue",
    "Net Profit",
    "EPS",
    "Sales Growth",
    "Dividend Yield",
    "P/E",
    "P/B",
    "Market Cap",
    "Composite Score",
    "Debt-Free",
]


PERCENTILE_COLUMNS = [
    "ROE Percentile",
    "ROCE Percentile",
    "NPM Percentile",
    "D/E Percentile",
    "FCF Percentile",
    "PAT CAGR 5yr Percentile",
    "Revenue CAGR 5yr Percentile",
    "EPS CAGR 5yr Percentile",
    "Interest Coverage Percentile",
    "Asset Turnover Percentile",
]


# ============================================================
# LOAD DATA
# ============================================================

def load_data():

    conn = sqlite3.connect(DB_PATH)

    # --------------------------------------------------------
    # Peer percentile data
    # --------------------------------------------------------

    percentile_df = pd.read_sql_query(
        """
        SELECT
            pp.company_id,
            pp.peer_group_name,
            pp.metric,
            pp.value,
            pp.percentile_rank,
            pp.year,
            c.company_name
        FROM peer_percentiles pp
        JOIN companies c
            ON c.id = pp.company_id
        """,
        conn,
    )

    # --------------------------------------------------------
    # Peer group master data
    # --------------------------------------------------------

    peer_group_df = pd.read_sql_query(
        """
        SELECT
            company_id,
            peer_group_name,
            is_benchmark
        FROM peer_groups
        """,
        conn,
    )

    # --------------------------------------------------------
    # Latest financial ratios
    # --------------------------------------------------------

    ratios_df = pd.read_sql_query(
        """
        SELECT
            fr.company_id,
            fr.year,
            fr.revenue_cagr_5yr,
            fr.pat_cagr_5yr,
            fr.eps_cagr_5yr,
            fr.composite_quality_score,
            fr.total_debt_cr,
            fr.debt_to_equity,
            fr.interest_coverage,
            fr.return_on_equity,
            fr.return_on_capital,
            fr.net_profit_margin,
            fr.free_cash_flow,
            fr.asset_turnover,
            fr.earnings_per_share,
            fr.high_leverage_flag
        FROM financial_ratios fr
        WHERE fr.year = (
            SELECT MAX(fr2.year)
            FROM financial_ratios fr2
            WHERE fr2.company_id = fr.company_id
        )
        """,
        conn,
    )

    # --------------------------------------------------------
    # P&L
    # --------------------------------------------------------

    pnl_df = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            sales,
            net_profit,
            eps
        FROM profitandloss
        WHERE year = (
            SELECT MAX(p2.year)
            FROM profitandloss p2
            WHERE p2.company_id = profitandloss.company_id
        )
        """,
        conn,
    )

    # --------------------------------------------------------
    # Market data
    # --------------------------------------------------------

    market_df = pd.read_sql_query(
        """
        SELECT
            company_id,
            year,
            market_cap_crore,
            pe_ratio,
            pb_ratio,
            dividend_yield_pct
        FROM market_cap
        WHERE year = (
            SELECT MAX(m2.year)
            FROM market_cap m2
            WHERE m2.company_id = market_cap.company_id
        )
        """,
        conn,
    )

    conn.close()

    return (
        percentile_df,
        peer_group_df,
        ratios_df,
        pnl_df,
        market_df,
    )


# ============================================================
# PREPARE COMPANY DATA
# ============================================================

def prepare_company_data(
    percentile_df,
    ratios_df,
    pnl_df,
    market_df,
):

    ratios = ratios_df.copy()

    pnl = pnl_df.copy()

    # --------------------------------------------------------
    # Sales growth
    # --------------------------------------------------------

    pnl = pnl.sort_values(
        ["company_id", "year"]
    )

    pnl["sales_growth"] = (
        pnl.groupby("company_id")["sales"]
        .pct_change()
        * 100
    )

    latest_pnl = (
        pnl.sort_values("year")
        .groupby("company_id")
        .tail(1)
    )

    market = market_df.copy()

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    base = ratios.merge(
        latest_pnl[
            [
                "company_id",
                "sales",
                "net_profit",
                "eps",
                "sales_growth",
            ]
        ],
        on="company_id",
        how="left",
    )

    base = base.merge(
        market[
            [
                "company_id",
                "market_cap_crore",
                "pe_ratio",
                "pb_ratio",
                "dividend_yield_pct",
            ]
        ],
        on="company_id",
        how="left",
    )

    return base


# ============================================================
# DEBT-FREE HELPER
# ============================================================

def np_where_debt_free(series):

    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    return values.fillna(0).eq(0).map(
        {
            True: "Yes",
            False: "No",
        }
    )


# ============================================================
# BUILD PEER SHEET
# ============================================================

def build_peer_sheet(
    peer_group,
    percentile_df,
    peer_group_df,
    company_data,
):

    group_df = percentile_df[
        percentile_df["peer_group_name"] == peer_group
    ].copy()

    company_ids = (
        group_df["company_id"]
        .astype(str)
        .unique()
    )

    # --------------------------------------------------------
    # Company names
    # --------------------------------------------------------

    company_names = (
        group_df[
            ["company_id", "company_name"]
        ]
        .drop_duplicates("company_id")
    )

    # --------------------------------------------------------
    # Percentile pivot
    # --------------------------------------------------------

    percentile_pivot = group_df.pivot_table(
        index="company_id",
        columns="metric",
        values="percentile_rank",
        aggfunc="first",
    ).reset_index()

    percentile_pivot["company_id"] = (
        percentile_pivot["company_id"]
        .astype(str)
    )

    # --------------------------------------------------------
    # Raw company data
    # --------------------------------------------------------

    raw = company_data.copy()

    raw["company_id"] = (
        raw["company_id"]
        .astype(str)
    )

    raw = raw[
        raw["company_id"].isin(company_ids)
    ]

    # --------------------------------------------------------
    # Company names
    # --------------------------------------------------------

    raw = raw.merge(
        company_names,
        on="company_id",
        how="left",
    )

    # --------------------------------------------------------
    # Percentile data
    # --------------------------------------------------------

    result = raw.merge(
        percentile_pivot,
        on="company_id",
        how="left",
        suffixes=("", "_percentile"),
    )

    # --------------------------------------------------------
    # Rename percentile columns
    # --------------------------------------------------------

    rename_map = {
        "ROE": "ROE Percentile",
        "ROCE": "ROCE Percentile",
        "NPM": "NPM Percentile",
        "D/E": "D/E Percentile",
        "FCF": "FCF Percentile",
        "PAT CAGR 5yr": "PAT CAGR 5yr Percentile",
        "Revenue CAGR 5yr": "Revenue CAGR 5yr Percentile",
        "EPS CAGR 5yr": "EPS CAGR 5yr Percentile",
        "Interest Coverage": "Interest Coverage Percentile",
        "Asset Turnover": "Asset Turnover Percentile",
    }

    result = result.rename(
        columns=rename_map
    )

    # --------------------------------------------------------
    # Create final company dataframe
    # --------------------------------------------------------

    final = pd.DataFrame()

    final["company_id"] = result["company_id"]
    final["company_name"] = result["company_name"]

    final["ROE"] = result["return_on_equity"]
    final["ROCE"] = result["return_on_capital"]
    final["NPM"] = result["net_profit_margin"]
    final["D/E"] = result["debt_to_equity"]
    final["FCF"] = result["free_cash_flow"]
    final["PAT CAGR 5yr"] = result["pat_cagr_5yr"]
    final["Revenue CAGR 5yr"] = result["revenue_cagr_5yr"]
    final["EPS CAGR 5yr"] = result["eps_cagr_5yr"]
    final["Interest Coverage"] = result["interest_coverage"]
    final["Asset Turnover"] = result["asset_turnover"]

    final["Revenue"] = result["sales"]
    final["Net Profit"] = result["net_profit"]
    final["EPS"] = result["earnings_per_share"]
    final["Sales Growth"] = result["sales_growth"]
    final["Dividend Yield"] = result["dividend_yield_pct"]
    final["P/E"] = result["pe_ratio"]
    final["P/B"] = result["pb_ratio"]
    final["Market Cap"] = result["market_cap_crore"]
    final["Composite Score"] = result["composite_quality_score"]

    final["Debt-Free"] = np_where_debt_free(
        result["debt_to_equity"]
    )

    # --------------------------------------------------------
    # Percentile columns
    # --------------------------------------------------------

    for col in PERCENTILE_COLUMNS:

        if col in result.columns:
            final[col] = result[col]
        else:
            final[col] = None

    # --------------------------------------------------------
    # Sort company rows
    # --------------------------------------------------------

    final = final.sort_values(
        "Composite Score",
        ascending=False,
        na_position="last",
    ).reset_index(drop=True)

    # ========================================================
    # BENCHMARK ROW
    # ========================================================

    peer_meta = peer_group_df[
        peer_group_df["peer_group_name"] == peer_group
    ].copy()

    peer_meta["company_id"] = (
        peer_meta["company_id"]
        .astype(str)
    )

    benchmark_ids = peer_meta.loc[
        peer_meta["is_benchmark"].astype(str).str.lower().isin(
            ["1", "true", "yes"]
        ),
        "company_id",
    ].tolist()

    benchmark_row = None

    if benchmark_ids:

        benchmark_company_id = benchmark_ids[0]

        benchmark_matches = final[
            final["company_id"].astype(str)
            == benchmark_company_id
        ]

        if not benchmark_matches.empty:
            benchmark_row = benchmark_matches.iloc[0].copy()

    # If no explicit benchmark exists, use peer-group median
    # as a safe fallback.
    if benchmark_row is None:

        numeric_cols = [
            col for col in final.columns
            if col not in ["company_id", "company_name", "Debt-Free"]
        ]

        benchmark_row = final.iloc[0].copy()

        benchmark_row["company_id"] = "BENCHMARK"
        benchmark_row["company_name"] = (
            f"{peer_group} Benchmark"
        )

        for col in numeric_cols:
            benchmark_row[col] = pd.to_numeric(
                final[col],
                errors="coerce",
            ).median()

        benchmark_row["Debt-Free"] = ""

    else:
        benchmark_row = benchmark_row.copy()
        benchmark_row["company_id"] = "BENCHMARK"
        benchmark_row["company_name"] = (
            f"{peer_group} Benchmark"
        )

    # ========================================================
    # MEDIAN / SUMMARY ROW
    # ========================================================

    median_row = {
        col: None
        for col in final.columns
    }

    median_row["company_id"] = "SUMMARY"
    median_row["company_name"] = "Peer Group Median"

    numeric_columns = [
        col for col in final.columns
        if col not in [
            "company_id",
            "company_name",
            "Debt-Free",
        ]
    ]

    for col in numeric_columns:

        median_row[col] = pd.to_numeric(
            final[col],
            errors="coerce",
        ).median()

    median_row["Debt-Free"] = ""

    median_row = pd.Series(
        median_row
    )

    # --------------------------------------------------------
    # Place rows:
    # Company rows
    # Benchmark
    # Summary
    # --------------------------------------------------------

    final = pd.concat(
        [
            final,
            pd.DataFrame([benchmark_row]),
            pd.DataFrame([median_row]),
        ],
        ignore_index=True,
    )

    return final


# ============================================================
# EXCEL FORMATTING
# ============================================================

def format_workbook(output_file):

    wb = load_workbook(
        output_file
    )

    # --------------------------------------------------------
    # Fills
    # --------------------------------------------------------

    header_fill = PatternFill(
        fill_type="solid",
        fgColor="1F4E78",
    )

    green_fill = PatternFill(
        fill_type="solid",
        fgColor="C6EFCE",
    )

    yellow_fill = PatternFill(
        fill_type="solid",
        fgColor="FFEB9C",
    )

    red_fill = PatternFill(
        fill_type="solid",
        fgColor="FFC7CE",
    )

    benchmark_fill = PatternFill(
        fill_type="solid",
        fgColor="FFD966",
    )

    median_fill = PatternFill(
        fill_type="solid",
        fgColor="D9EAD3",
    )

    white_font = Font(
        color="FFFFFF",
        bold=True,
    )

    bold_font = Font(
        bold=True
    )

    # --------------------------------------------------------
    # Process sheets
    # --------------------------------------------------------

    for ws in wb.worksheets:

        # Header
        for cell in ws[1]:

            cell.fill = header_fill
            cell.font = white_font
            cell.alignment = Alignment(
                horizontal="center",
                vertical="center",
            )

        ws.freeze_panes = "C2"

        # ----------------------------------------------------
        # Find percentile columns
        # ----------------------------------------------------

        percentile_cols = []

        for col in range(
            1,
            ws.max_column + 1,
        ):

            header = ws.cell(
                row=1,
                column=col,
            ).value

            if (
                header
                and "Percentile" in str(header)
            ):
                percentile_cols.append(col)

        # ----------------------------------------------------
        # Identify benchmark and summary rows
        # ----------------------------------------------------

        benchmark_row_num = None
        median_row_num = None

        for row in range(
            2,
            ws.max_row + 1,
        ):

            company_id = ws.cell(
                row=row,
                column=1,
            ).value

            if company_id == "BENCHMARK":
                benchmark_row_num = row

            elif company_id == "SUMMARY":
                median_row_num = row

        # ----------------------------------------------------
        # Percentile coloring
        # Only company rows
        # ----------------------------------------------------

        for row in range(
            2,
            ws.max_row + 1,
        ):

            if row in [
                benchmark_row_num,
                median_row_num,
            ]:
                continue

            for col in percentile_cols:

                cell = ws.cell(
                    row=row,
                    column=col,
                )

                try:
                    value = float(
                        cell.value
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    continue

                if value >= 75:
                    cell.fill = green_fill

                elif value >= 25:
                    cell.fill = yellow_fill

                else:
                    cell.fill = red_fill

        # ----------------------------------------------------
        # Benchmark row formatting
        # ----------------------------------------------------

        if benchmark_row_num:

            for col in range(
                1,
                ws.max_column + 1,
            ):

                cell = ws.cell(
                    row=benchmark_row_num,
                    column=col,
                )

                cell.fill = benchmark_fill
                cell.font = bold_font

        # ----------------------------------------------------
        # Median / Summary row formatting
        # ----------------------------------------------------

        if median_row_num:

            for col in range(
                1,
                ws.max_column + 1,
            ):

                cell = ws.cell(
                    row=median_row_num,
                    column=col,
                )

                cell.fill = median_fill
                cell.font = bold_font

        # ----------------------------------------------------
        # Number formats
        # ----------------------------------------------------

        for row in ws.iter_rows(
            min_row=2
        ):

            for cell in row:

                if isinstance(
                    cell.value,
                    (int, float),
                ):

                    cell.number_format = (
                        '#,##0.00'
                    )

        # ----------------------------------------------------
        # Column widths
        # ----------------------------------------------------

        for col in range(
            1,
            ws.max_column + 1,
        ):

            letter = get_column_letter(
                col
            )

            max_length = 0

            for cell in ws[letter]:

                if cell.value is not None:

                    max_length = max(
                        max_length,
                        len(str(cell.value)),
                    )

            ws.column_dimensions[
                letter
            ].width = min(
                max(max_length + 2, 12),
                30,
            )

        ws.row_dimensions[1].height = 25

        # ----------------------------------------------------
        # Autofilter only over company data
        # ----------------------------------------------------

        if benchmark_row_num:
            ws.auto_filter.ref = (
                f"A1:{get_column_letter(ws.max_column)}"
                f"{benchmark_row_num - 1}"
            )
        else:
            ws.auto_filter.ref = ws.dimensions

    wb.save(output_file)


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("NIFTY 100 PEER COMPARISON EXCEL")
    print("=" * 60)

    # --------------------------------------------------------
    # Load
    # --------------------------------------------------------

    (
        percentile_df,
        peer_group_df,
        ratios_df,
        pnl_df,
        market_df,
    ) = load_data()

    # --------------------------------------------------------
    # Prepare
    # --------------------------------------------------------

    company_data = prepare_company_data(
        percentile_df,
        ratios_df,
        pnl_df,
        market_df,
    )

    # --------------------------------------------------------
    # Peer groups
    # --------------------------------------------------------

    peer_groups = sorted(
        percentile_df[
            "peer_group_name"
        ]
        .dropna()
        .unique()
    )

    print(
        f"Peer groups found: "
        f"{len(peer_groups)}"
    )

    # --------------------------------------------------------
    # Ensure output folder
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Create Excel
    # --------------------------------------------------------

    with pd.ExcelWriter(
        OUTPUT_FILE,
        engine="openpyxl",
    ) as writer:

        for peer_group in peer_groups:

            print(
                f"Creating sheet: "
                f"{peer_group}"
            )

            sheet_df = build_peer_sheet(
                peer_group,
                percentile_df,
                peer_group_df,
                company_data,
            )

            sheet_name = str(
                peer_group
            )[:31]

            sheet_df.to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )

    # --------------------------------------------------------
    # Format
    # --------------------------------------------------------

    format_workbook(
        OUTPUT_FILE
    )

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    wb = load_workbook(
        OUTPUT_FILE,
        read_only=True,
    )

    print()
    print("=" * 60)
    print("PEER COMPARISON EXPORT COMPLETED")
    print("=" * 60)

    print(
        f"File: {OUTPUT_FILE}"
    )

    print(
        f"Sheets created: "
        f"{len(wb.sheetnames)}"
    )

    print("Sheets:")

    for sheet in wb.sheetnames:
        print(
            f"  - {sheet}"
        )

    print("=" * 60)

    wb.close()


if __name__ == "__main__":
    main()