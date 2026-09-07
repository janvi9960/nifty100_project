import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import (
    get_companies,
    get_peers,
    get_ratios,
    get_valuation,
)


st.title("👥 Peer Comparison")
st.caption("Compare companies with their industry peers")


# ---------------------------------------------------------
# LOAD COMPANY DATA
# ---------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("Company data is not available.")
    st.stop()


# ---------------------------------------------------------
# PEER GROUPS
# ---------------------------------------------------------

peer_groups = [
    "Automobiles",
    "Consumer Finance",
    "FMCG",
    "IT Services",
    "Life Insurance",
    "Oil & Gas",
    "Pharmaceuticals",
    "Power & Utilities",
    "Private Banks",
    "Public Sector Banks",
    "Steel",
]


selected_group = st.selectbox(
    "🏷️ Select Peer Group",
    peer_groups
)


peers = get_peers(selected_group)

if peers.empty:
    st.warning("No companies found for this peer group.")
    st.stop()


# ---------------------------------------------------------
# COMPANY SELECTION
# ---------------------------------------------------------

peer_options = peers.apply(
    lambda row: f"{row['company_name']} ({row['company_id']})",
    axis=1
).tolist()


selected_display = st.selectbox(
    "🔎 Select Company",
    peer_options
)


selected_ticker = selected_display.split("(")[-1].replace(")", "")


# ---------------------------------------------------------
# LOAD METRICS FOR PEER COMPANIES
# ---------------------------------------------------------

peer_metrics = []

for ticker in peers["company_id"]:

    ratio_df = get_ratios(ticker)

    valuation_df = get_valuation(ticker)

    if ratio_df.empty:
        continue

    latest_ratio = ratio_df.sort_values("year").iloc[-1]

    if not valuation_df.empty:
        latest_valuation = valuation_df.sort_values("year").iloc[-1]

        pe = latest_valuation["pe_ratio"]
        pb = latest_valuation["pb_ratio"]
    else:
        pe = None
        pb = None

    peer_metrics.append(
        {
            "company_id": ticker,
            "company_name": peers.loc[
                peers["company_id"] == ticker,
                "company_name"
            ].iloc[0],
            "is_benchmark": bool(
                peers.loc[
                    peers["company_id"] == ticker,
                    "is_benchmark"
                ].iloc[0]
            ),
            "ROE": latest_ratio.get("return_on_equity"),
            "ROCE": latest_ratio.get("return_on_capital"),
            "NPM": latest_ratio.get("net_profit_margin"),
            "D/E": latest_ratio.get("debt_to_equity"),
            "Revenue CAGR": latest_ratio.get("revenue_cagr_5yr"),
            "PAT CAGR": latest_ratio.get("pat_cagr_5yr"),
            "Interest Coverage": latest_ratio.get("interest_coverage"),
            "P/E": pe,
            "P/B": pb,
        }
    )


metrics_df = pd.DataFrame(peer_metrics)

if metrics_df.empty:
    st.warning("Peer financial data is not available.")
    st.stop()


# ---------------------------------------------------------
# SELECTED COMPANY
# ---------------------------------------------------------

selected_row = metrics_df[
    metrics_df["company_id"] == selected_ticker
]

if selected_row.empty:
    st.warning("Selected company data is not available.")
    st.stop()

selected = selected_row.iloc[0]


# ---------------------------------------------------------
# PEER AVERAGE
# ---------------------------------------------------------

metric_columns = [
    "ROE",
    "ROCE",
    "NPM",
    "D/E",
    "Revenue CAGR",
    "PAT CAGR",
    "Interest Coverage",
    "P/E",
]


peer_average = metrics_df[
    metrics_df["company_id"] != selected_ticker
][metric_columns].mean(numeric_only=True)


# ---------------------------------------------------------
# RADAR CHART
# ---------------------------------------------------------

st.subheader("📊 Peer Radar Comparison")

radar_metrics = [
    "ROE",
    "ROCE",
    "NPM",
    "Revenue CAGR",
    "PAT CAGR",
    "Interest Coverage",
    "P/E",
    "P/B",
]


selected_values = []

peer_average_values = []

for metric in radar_metrics:

    selected_value = selected[metric]

    if pd.isna(selected_value):
        selected_value = 0

    selected_values.append(float(selected_value))

    if metric in peer_average.index:
        average_value = peer_average[metric]
    else:
        average_value = metrics_df[
            metrics_df["company_id"] != selected_ticker
        ][metric].mean()

    if pd.isna(average_value):
        average_value = 0

    peer_average_values.append(float(average_value))


radar = go.Figure()


radar.add_trace(
    go.Scatterpolar(
        r=selected_values + [selected_values[0]],
        theta=radar_metrics + [radar_metrics[0]],
        fill="toself",
        name=selected["company_name"],
    )
)


radar.add_trace(
    go.Scatterpolar(
        r=peer_average_values + [peer_average_values[0]],
        theta=radar_metrics + [radar_metrics[0]],
        fill="toself",
        name="Peer Average",
    )
)


radar.update_layout(
    polar=dict(
        radialaxis=dict(
            visible=True
        )
    ),
    showlegend=True,
    height=550,
)


st.plotly_chart(
    radar,
    use_container_width=True
)


# ---------------------------------------------------------
# KPI TABLE
# ---------------------------------------------------------

st.subheader("📋 Peer KPI Comparison")

display_df = metrics_df[
    [
        "company_id",
        "company_name",
        "is_benchmark",
        "ROE",
        "ROCE",
        "NPM",
        "D/E",
        "Revenue CAGR",
        "PAT CAGR",
        "Interest Coverage",
        "P/E",
        "P/B",
    ]
].copy()


display_df = display_df.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "is_benchmark": "Benchmark",
    }
)


# Round numerical columns
numeric_columns = display_df.select_dtypes(
    include="number"
).columns

display_df[numeric_columns] = display_df[numeric_columns].round(2)


# Highlight benchmark company
def highlight_benchmark(row):
    if row["Benchmark"]:
        return [
            "font-weight: bold"
            for _ in row
        ]

    return [""] * len(row)


styled_df = display_df.style.apply(
    highlight_benchmark,
    axis=1
)


st.dataframe(
    styled_df,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# PEER SUMMARY
# ---------------------------------------------------------

st.subheader("📌 Peer Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Peer Group",
        selected_group
    )

with col2:
    st.metric(
        "Companies",
        len(metrics_df)
    )

with col3:
    benchmark = metrics_df[
        metrics_df["is_benchmark"]
    ]

    if not benchmark.empty:
        st.metric(
            "Benchmark",
            benchmark.iloc[0]["company_name"]
        )
    else:
        st.metric(
            "Benchmark",
            "N/A"
        )