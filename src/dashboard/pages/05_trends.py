import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_companies, get_ratios


st.title("📈 Financial Trends")
st.caption("Analyze long-term financial performance and year-over-year changes")


# ---------------------------------------------------------
# LOAD COMPANIES
# ---------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("Company data is not available.")
    st.stop()


# ---------------------------------------------------------
# COMPANY SEARCH
# ---------------------------------------------------------

company_options = companies.apply(
    lambda row: f"{row['company_name']} ({row['company_id']})",
    axis=1
).tolist()

selected_company = st.selectbox(
    "🔎 Search Company",
    company_options
)

selected_ticker = selected_company.split("(")[-1].replace(")", "")

company_row = companies[
    companies["company_id"] == selected_ticker
]

if company_row.empty:
    st.warning("Company not found.")
    st.stop()

company_name = company_row.iloc[0]["company_name"]


# ---------------------------------------------------------
# LOAD RATIO DATA
# ---------------------------------------------------------

ratios = get_ratios(selected_ticker)

if ratios.empty:
    st.warning(
        f"No financial ratio data is available for {company_name}."
    )
    st.stop()


ratios = ratios.sort_values("year").copy()

# Keep latest 10 available years
trend_data = ratios.tail(10).copy()


# ---------------------------------------------------------
# AVAILABLE METRICS
# ---------------------------------------------------------

metric_mapping = {
    "ROE (%)": "return_on_equity",
    "ROCE (%)": "return_on_capital",
    "Net Profit Margin (%)": "net_profit_margin",
    "Debt / Equity": "debt_to_equity",
    "Revenue CAGR 5yr (%)": "revenue_cagr_5yr",
    "PAT CAGR 5yr (%)": "pat_cagr_5yr",
    "EPS CAGR 5yr (%)": "eps_cagr_5yr",
    "Operating Profit Margin (%)": "operating_profit_margin",
    "Interest Coverage": "interest_coverage",
    "Free Cash Flow (₹ Cr)": "free_cash_flow",
    "Asset Turnover": "asset_turnover",
    "Earnings Per Share": "earnings_per_share",
    "Book Value Per Share": "book_value_per_share",
}


available_metrics = [
    label
    for label, column in metric_mapping.items()
    if column in trend_data.columns
]


# ---------------------------------------------------------
# METRIC SELECTOR
# ---------------------------------------------------------

st.subheader("📊 Select Metrics")

selected_metrics = st.multiselect(
    "Choose up to 3 metrics",
    available_metrics,
    default=available_metrics[:2],
    max_selections=3
)


if not selected_metrics:
    st.info("Please select at least one metric.")
    st.stop()


# ---------------------------------------------------------
# TREND CHART
# ---------------------------------------------------------

st.subheader(
    f"📈 10-Year Trend — {company_name}"
)

fig = go.Figure()


for metric in selected_metrics:

    column = metric_mapping[metric]

    values = pd.to_numeric(
        trend_data[column],
        errors="coerce"
    )

    fig.add_trace(
        go.Scatter(
            x=trend_data["year"],
            y=values,
            mode="lines+markers",
            name=metric,
            connectgaps=False
        )
    )


fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Value",
    hovermode="x unified",
    height=550,
    legend_title="Metrics"
)


st.plotly_chart(
    fig,
    use_container_width=True
)


# ---------------------------------------------------------
# YOY CHANGE TABLE
# ---------------------------------------------------------

st.subheader("📊 Year-over-Year Change")

yoy_data = pd.DataFrame()

yoy_data["Year"] = trend_data["year"].values


for metric in selected_metrics:

    column = metric_mapping[metric]

    values = pd.to_numeric(
        trend_data[column],
        errors="coerce"
    )

    yoy_change = values.pct_change() * 100

    yoy_data[metric] = yoy_change.round(2)


# ---------------------------------------------------------
# DISPLAY YOY TABLE
# ---------------------------------------------------------

display_yoy = yoy_data.copy()

for column in display_yoy.columns:
    if column != "Year":
        display_yoy[column] = display_yoy[column].apply(
            lambda x: "N/A"
            if pd.isna(x)
            else f"{x:.2f}%"
        )


st.dataframe(
    display_yoy,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# ANNOTATED YOY CHART
# ---------------------------------------------------------

st.subheader("📌 YoY % Change Annotations")


annotation_fig = go.Figure()


for metric in selected_metrics:

    column = metric_mapping[metric]

    values = pd.to_numeric(
        trend_data[column],
        errors="coerce"
    )

    yoy_change = values.pct_change() * 100

    annotation_text = []

    for value in yoy_change:

        if pd.isna(value):
            annotation_text.append("N/A")
        else:
            annotation_text.append(
                f"{value:+.1f}%"
            )

    annotation_fig.add_trace(
        go.Scatter(
            x=trend_data["year"],
            y=values,
            mode="lines+markers+text",
            name=metric,
            text=annotation_text,
            textposition="top center",
            connectgaps=False
        )
    )


annotation_fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Value",
    hovermode="x unified",
    height=600,
    legend_title="Metrics"
)


st.plotly_chart(
    annotation_fig,
    use_container_width=True
)


# ---------------------------------------------------------
# DATA AVAILABILITY
# ---------------------------------------------------------

st.caption(
    f"Showing {len(trend_data)} available years "
    f"for {company_name}."
)