from pathlib import Path
import sqlite3
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "radar_charts"


# ============================================================
# RADAR AXES
# ============================================================

METRICS = [
    "ROE",
    "ROCE",
    "NPM",
    "D/E",
    "FCF Score",
    "PAT CAGR 5yr",
    "Revenue CAGR 5yr",
    "Composite Score",
]


# Mapping radar metrics to peer_percentiles metrics
PEER_METRIC_MAP = {
    "ROE": "ROE",
    "ROCE": "ROCE",
    "NPM": "NPM",
    "D/E": "D/E",
    "FCF Score": "FCF",
    "PAT CAGR 5yr": "PAT CAGR 5yr",
    "Revenue CAGR 5yr": "Revenue CAGR 5yr",
}


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    conn = sqlite3.connect(DB_PATH)

    # Latest financial ratio row for every company
    ratios = pd.read_sql_query(
        """
        SELECT
            fr.company_id,
            c.company_name,
            fr.year,
            fr.return_on_equity,
            fr.return_on_capital,
            fr.net_profit_margin,
            fr.debt_to_equity,
            fr.free_cash_flow,
            fr.pat_cagr_5yr,
            fr.revenue_cagr_5yr,
            fr.composite_quality_score
        FROM financial_ratios fr
        JOIN companies c
            ON c.id = fr.company_id
        WHERE fr.year = (
            SELECT MAX(fr2.year)
            FROM financial_ratios fr2
            WHERE fr2.company_id = fr.company_id
        )
        """,
        conn,
    )

    # Peer percentile data
    peer_percentiles = pd.read_sql_query(
        """
        SELECT
            company_id,
            peer_group_name,
            metric,
            percentile_rank,
            year
        FROM peer_percentiles
        """,
        conn,
    )

    conn.close()

    return ratios, peer_percentiles


# ============================================================
# CLEAN COMPANY NAME FOR WINDOWS FILESYSTEM
# ============================================================

def clean_company_name(name):
    """
    Make company name safe for Windows filenames.

    Handles:
    - Newlines
    - Tabs
    - Multiple spaces
    - Invalid Windows filename characters
    - Trailing spaces and periods
    """

    name = str(name)

    # Replace newline/tab/multiple whitespace
    name = re.sub(r"\s+", " ", name).strip()

    # Replace Windows-invalid filename characters
    name = re.sub(r'[<>:"/\\|?*]', "_", name)

    # Remove trailing spaces and periods
    name = name.rstrip(". ")

    # Fallback
    if not name:
        name = "Unknown_Company"

    return name


# ============================================================
# PERCENTILE SCORE
# ============================================================

def percentile_score(series, higher_is_better=True):
    """
    Convert raw metric values into 0-100 percentile scores.

    Higher value is better by default.
    For D/E, lower value is better.
    """

    values = pd.to_numeric(
        series,
        errors="coerce",
    )

    if not higher_is_better:
        values = -values

    scores = values.rank(
        method="average",
        pct=True,
    ) * 100

    return scores.fillna(0)


# ============================================================
# BUILD NIFTY 100 UNIVERSE SCORES
# ============================================================

def build_universe_scores(ratios):
    """
    Build 0-100 scores for all 92 companies.

    These scores are used for:
    - Companies without peer groups
    - Nifty 100 average reference
    """

    scores = ratios[
        [
            "company_id",
            "company_name",
            "return_on_equity",
            "return_on_capital",
            "net_profit_margin",
            "debt_to_equity",
            "free_cash_flow",
            "pat_cagr_5yr",
            "revenue_cagr_5yr",
            "composite_quality_score",
        ]
    ].copy()

    # --------------------------------------------------------
    # Profitability
    # --------------------------------------------------------

    scores["ROE"] = percentile_score(
        scores["return_on_equity"]
    )

    scores["ROCE"] = percentile_score(
        scores["return_on_capital"]
    )

    scores["NPM"] = percentile_score(
        scores["net_profit_margin"]
    )

    # --------------------------------------------------------
    # Leverage
    # Lower D/E = better
    # --------------------------------------------------------

    scores["D/E"] = percentile_score(
        scores["debt_to_equity"],
        higher_is_better=False,
    )

    # --------------------------------------------------------
    # Cash Flow
    # --------------------------------------------------------

    scores["FCF Score"] = percentile_score(
        scores["free_cash_flow"]
    )

    # --------------------------------------------------------
    # Growth
    # --------------------------------------------------------

    scores["PAT CAGR 5yr"] = percentile_score(
        scores["pat_cagr_5yr"]
    )

    scores["Revenue CAGR 5yr"] = percentile_score(
        scores["revenue_cagr_5yr"]
    )

    # --------------------------------------------------------
    # Composite score
    # Already calculated on 0-100 scale
    # --------------------------------------------------------

    scores["Composite Score"] = pd.to_numeric(
        scores["composite_quality_score"],
        errors="coerce",
    ).fillna(0).clip(0, 100)

    return scores


# ============================================================
# GET COMPANY PEER VALUES
# ============================================================

def get_peer_company_values(
    company_id,
    peer_percentiles,
):
    """
    Get percentile values for a company from peer_percentiles.
    """

    company_rows = peer_percentiles[
        peer_percentiles["company_id"].astype(str)
        == str(company_id)
    ]

    values = {}

    for radar_metric, peer_metric in PEER_METRIC_MAP.items():

        row = company_rows[
            company_rows["metric"]
            .astype(str)
            .str.strip()
            == peer_metric
        ]

        if not row.empty:

            value = pd.to_numeric(
                row.iloc[0]["percentile_rank"],
                errors="coerce",
            )

            values[radar_metric] = (
                float(value)
                if pd.notna(value)
                else 0.0
            )

        else:
            values[radar_metric] = 0.0

    return values


# ============================================================
# GET PEER GROUP AVERAGE
# ============================================================

def get_peer_average(
    peer_group_name,
    peer_percentiles,
    metric_names,
):
    """
    Calculate average percentile score for a peer group.
    """

    group = peer_percentiles[
        peer_percentiles["peer_group_name"]
        == peer_group_name
    ]

    averages = {}

    for radar_metric, peer_metric in metric_names.items():

        rows = group[
            group["metric"]
            .astype(str)
            .str.strip()
            == peer_metric
        ]

        if rows.empty:

            averages[radar_metric] = 0.0

        else:

            values = pd.to_numeric(
                rows["percentile_rank"],
                errors="coerce",
            )

            averages[radar_metric] = float(
                values.mean()
            )

    return averages


# ============================================================
# CREATE RADAR CHART
# ============================================================

def create_radar(
    company_name,
    company_values,
    reference_values,
    reference_label,
    output_path,
):
    """
    Create and save a radar chart.
    """

    labels = METRICS

    # Company values
    company_data = [
        float(
            company_values.get(metric, 0)
        )
        for metric in labels
    ]

    # Reference values
    reference_data = [
        float(
            reference_values.get(metric, 0)
        )
        for metric in labels
    ]

    # --------------------------------------------------------
    # Radar angles
    # --------------------------------------------------------

    angles = np.linspace(
        0,
        2 * np.pi,
        len(labels),
        endpoint=False,
    ).tolist()

    # Close polygons
    company_data += company_data[:1]
    reference_data += reference_data[:1]
    angles += angles[:1]

    # --------------------------------------------------------
    # Create figure
    # --------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(9, 9),
        subplot_kw=dict(polar=True),
    )

    ax.set_theta_offset(
        np.pi / 2
    )

    ax.set_theta_direction(
        -1
    )

    # --------------------------------------------------------
    # Company polygon
    # --------------------------------------------------------

    ax.plot(
        angles,
        company_data,
        linewidth=2,
        label=company_name,
    )

    ax.fill(
        angles,
        company_data,
        alpha=0.20,
    )

    # --------------------------------------------------------
    # Reference polygon
    # --------------------------------------------------------

    ax.plot(
        angles,
        reference_data,
        linestyle="--",
        linewidth=2,
        label=reference_label,
    )

    # --------------------------------------------------------
    # Axis labels
    # --------------------------------------------------------

    ax.set_xticks(
        angles[:-1]
    )

    ax.set_xticklabels(
        labels,
        fontsize=9,
    )

    # --------------------------------------------------------
    # Y-axis
    # --------------------------------------------------------

    ax.set_ylim(
        0,
        100,
    )

    ax.set_yticks(
        [
            20,
            40,
            60,
            80,
            100,
        ]
    )

    ax.set_yticklabels(
        [
            "20",
            "40",
            "60",
            "80",
            "100",
        ],
        fontsize=8,
    )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    ax.set_title(
        f"{company_name}\n"
        f"Peer / Nifty 100 Radar Comparison",
        fontsize=14,
        pad=25,
    )

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(
            1.30,
            1.10,
        ),
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    plt.tight_layout()

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close()


# ============================================================
# MAIN GENERATOR
# ============================================================

def generate_radar_charts():

    print("=" * 60)
    print("NIFTY 100 PEER RADAR CHART GENERATOR")
    print("=" * 60)

    # --------------------------------------------------------
    # Create output directory
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    ratios, peer_percentiles = load_data()

    print(
        f"Companies in latest ratio data: "
        f"{len(ratios)}"
    )

    # --------------------------------------------------------
    # Companies having peer data
    # --------------------------------------------------------

    peer_company_ids = set(
        peer_percentiles[
            "company_id"
        ]
        .astype(str)
        .unique()
    )

    print(
        f"Companies with peer data: "
        f"{len(peer_company_ids)}"
    )

    # --------------------------------------------------------
    # Peer groups
    # --------------------------------------------------------

    peer_groups = sorted(
        peer_percentiles[
            "peer_group_name"
        ]
        .dropna()
        .unique()
    )

    print(
        f"Peer groups: "
        f"{len(peer_groups)}"
    )

    # --------------------------------------------------------
    # Build Nifty 100 scores
    # --------------------------------------------------------

    universe_scores = build_universe_scores(
        ratios
    )

    # --------------------------------------------------------
    # Nifty 100 average
    # --------------------------------------------------------

    nifty_average = {
        metric: float(
            universe_scores[metric].mean()
        )
        for metric in METRICS
    }

    # --------------------------------------------------------
    # Generate charts
    # --------------------------------------------------------

    charts_generated = 0

    for _, company in ratios.iterrows():

        company_id = str(
            company["company_id"]
        )

        company_name = str(
            company["company_name"]
        )

        # ----------------------------------------------------
        # Safe filename
        # ----------------------------------------------------

        safe_name = clean_company_name(
            company_name
        )

        filename = (
            safe_name
            + "_radar.png"
        )

        output_path = (
            OUTPUT_DIR
            / filename
        )

        # ----------------------------------------------------
        # COMPANY WITH PEER GROUP
        # ----------------------------------------------------

        if company_id in peer_company_ids:

            company_values = (
                get_peer_company_values(
                    company_id,
                    peer_percentiles,
                )
            )

            # Composite Score
            composite = pd.to_numeric(
                company[
                    "composite_quality_score"
                ],
                errors="coerce",
            )

            company_values[
                "Composite Score"
            ] = (
                float(composite)
                if pd.notna(composite)
                else 0.0
            )

            # Find peer group
            company_peer_rows = (
                peer_percentiles[
                    peer_percentiles[
                        "company_id"
                    ].astype(str)
                    == company_id
                ]
            )

            peer_group = str(
                company_peer_rows[
                    "peer_group_name"
                ].iloc[0]
            )

            # ------------------------------------------------
            # Peer average
            # ------------------------------------------------

            reference_values = (
                get_peer_average(
                    peer_group,
                    peer_percentiles,
                    PEER_METRIC_MAP,
                )
            )

            # ------------------------------------------------
            # Composite Score peer average
            # ------------------------------------------------

            peer_ids = (
                peer_percentiles[
                    peer_percentiles[
                        "peer_group_name"
                    ]
                    == peer_group
                ]["company_id"]
                .astype(str)
                .unique()
            )

            peer_composite = (
                universe_scores[
                    universe_scores[
                        "company_id"
                    ]
                    .astype(str)
                    .isin(peer_ids)
                ]["Composite Score"]
                .mean()
            )

            reference_values[
                "Composite Score"
            ] = (
                float(peer_composite)
                if pd.notna(peer_composite)
                else 0.0
            )

            reference_label = (
                f"{peer_group} Average"
            )

        # ----------------------------------------------------
        # COMPANY WITHOUT PEER GROUP
        # ----------------------------------------------------

        else:

            universe_row = (
                universe_scores[
                    universe_scores[
                        "company_id"
                    ]
                    .astype(str)
                    == company_id
                ]
            )

            if universe_row.empty:
                print(
                    f"WARNING: No score data for "
                    f"{company_name}"
                )
                continue

            universe_row = (
                universe_row.iloc[0]
            )

            company_values = {
                metric: float(
                    universe_row[metric]
                )
                for metric in METRICS
            }

            reference_values = (
                nifty_average.copy()
            )

            reference_label = (
                "Nifty 100 Average"
            )

        # ----------------------------------------------------
        # Create radar chart
        # ----------------------------------------------------

        create_radar(
            company_name=company_name,
            company_values=company_values,
            reference_values=reference_values,
            reference_label=reference_label,
            output_path=output_path,
        )

        charts_generated += 1

    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print()
    print("=" * 60)
    print("RADAR CHART GENERATION COMPLETED")
    print("=" * 60)

    print(
        f"Charts generated: "
        f"{charts_generated}"
    )

    print(
        f"Expected companies: "
        f"{len(ratios)}"
    )

    print(
        f"Output directory: "
        f"{OUTPUT_DIR}"
    )

    print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    generate_radar_charts()
    