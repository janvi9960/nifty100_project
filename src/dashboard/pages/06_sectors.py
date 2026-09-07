import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import (
    get_companies,
    get_pl,
    get_ratios,
    get_valuation,
)


st.title("🏭 Sector Analysis")
st.caption("Compare companies and financial performance across sectors")


# ---------------------------------------------------------
# LOAD COMPANY DATA
# ---------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("Company data is not available.")
    st.stop()

companies["broad_sector"] = companies["broad_sector"].fillna("Unknown")
companies["sub_sector"] = companies["sub_sector"].fillna("Unknown")


# ---------------------------------------------------------
# SECTOR SELECTION
# ---------------------------------------------------------

sector_list = sorted(
    companies["broad_sector"].dropna().unique().tolist()
)

selected_sector = st.selectbox(
    "🏭 Select Sector",
    sector_list
)

sector_companies = companies[
    companies["broad_sector"] == selected_sector
].copy()

if sector_companies.empty:
    st.warning("No companies found for this sector.")
    st.stop()


# ---------------------------------------------------------
# LOAD FINANCIAL DATA
# ---------------------------------------------------------

financial_rows = []

for ticker in sector_companies["company_id"]:

    ratio_df = get_ratios(ticker)
    pl_df = get_pl(ticker)
    valuation_df = get_valuation(ticker)

    if ratio_df.empty:
        continue

    # Latest ratio data
    latest_ratio = ratio_df.sort_values("year").iloc[-1]

    # Latest P&L data for Revenue
    revenue = None

    if not pl_df.empty:
        latest_pl = pl_df.sort_values("year").iloc[-1]
        revenue = latest_pl.get("sales")

    # Latest market valuation
    market_cap = None

    if not valuation_df.empty:
        latest_valuation = (
            valuation_df.sort_values("year").iloc[-1]
        )

        market_cap = latest_valuation["market_cap_crore"]

    # Company name
    company_match = sector_companies[
        sector_companies["company_id"] == ticker
    ]

    if company_match.empty:
        continue

    company_name = company_match["company_name"].iloc[0]
    sub_sector = company_match["sub_sector"].iloc[0]

    financial_rows.append(
        {
            "company_id": ticker,
            "company_name": company_name,
            "sub_sector": sub_sector,

            # Revenue comes from P&L table
            "Revenue": revenue,

            # Ratios come from financial_ratios table
            "ROE": latest_ratio.get("return_on_equity"),
            "ROCE": latest_ratio.get("return_on_capital"),
            "Net Profit Margin": latest_ratio.get(
                "net_profit_margin"
            ),
            "Debt / Equity": latest_ratio.get(
                "debt_to_equity"
            ),
            "Revenue CAGR 5yr": latest_ratio.get(
                "revenue_cagr_5yr"
            ),
            "PAT CAGR 5yr": latest_ratio.get(
                "pat_cagr_5yr"
            ),

            # Market valuation
            "Market Cap": market_cap,
        }
    )


sector_data = pd.DataFrame(financial_rows)

if sector_data.empty:
    st.warning(
        f"Financial data is not available for {selected_sector}."
    )
    st.stop()


# ---------------------------------------------------------
# CONVERT NUMERIC COLUMNS
# ---------------------------------------------------------

numeric_columns = [
    "Revenue",
    "ROE",
    "ROCE",
    "Net Profit Margin",
    "Debt / Equity",
    "Revenue CAGR 5yr",
    "PAT CAGR 5yr",
    "Market Cap",
]

for column in numeric_columns:
    sector_data[column] = pd.to_numeric(
        sector_data[column],
        errors="coerce"
    )


# ---------------------------------------------------------
# SECTOR SUMMARY
# ---------------------------------------------------------

st.subheader(
    f"📊 {selected_sector} — Overview"
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Companies",
        len(sector_data)
    )

with col2:
    median_roe = sector_data["ROE"].median()

    if pd.notna(median_roe):
        st.metric(
            "Median ROE",
            f"{median_roe:.2f}%"
        )
    else:
        st.metric(
            "Median ROE",
            "N/A"
        )

with col3:
    median_de = sector_data["Debt / Equity"].median()

    if pd.notna(median_de):
        st.metric(
            "Median D/E",
            f"{median_de:.2f}"
        )
    else:
        st.metric(
            "Median D/E",
            "N/A"
        )

with col4:
    median_cagr = sector_data["Revenue CAGR 5yr"].median()

    if pd.notna(median_cagr):
        st.metric(
            "Median Revenue CAGR",
            f"{median_cagr:.2f}%"
        )
    else:
        st.metric(
            "Median Revenue CAGR",
            "N/A"
        )


# ---------------------------------------------------------
# REVENUE VS ROE BUBBLE CHART
# ---------------------------------------------------------

st.divider()

st.subheader("🫧 Revenue vs ROE")

bubble_data = sector_data.copy()

bubble_data = bubble_data.dropna(
    subset=["Revenue", "ROE"]
)

if bubble_data.empty:

    st.info(
        "Revenue and ROE data is not available for this sector."
    )

else:

    # Avoid invalid or zero bubble sizes
    bubble_data["Bubble Size"] = (
        bubble_data["Market Cap"]
        .fillna(1)
        .clip(lower=1)
    )

    fig_bubble = px.scatter(
        bubble_data,
        x="Revenue",
        y="ROE",
        size="Bubble Size",
        color="sub_sector",
        hover_name="company_name",
        hover_data={
            "company_id": True,
            "Revenue": ":,.2f",
            "ROE": ":.2f",
            "Market Cap": ":,.2f",
            "sub_sector": True,
            "Bubble Size": False,
        },
        title=f"{selected_sector}: Revenue vs ROE",
    )

    fig_bubble.update_layout(
        xaxis_title="Revenue (₹ Cr)",
        yaxis_title="ROE (%)",
        height=600,
    )

    st.plotly_chart(
        fig_bubble,
        use_container_width=True
    )


# ---------------------------------------------------------
# SECTOR MEDIAN KPI CHART
# ---------------------------------------------------------

st.divider()

st.subheader("📊 Sector Median KPIs")

kpi_columns = [
    "ROE",
    "ROCE",
    "Net Profit Margin",
    "Revenue CAGR 5yr",
    "PAT CAGR 5yr",
]

median_values = []

for metric in kpi_columns:

    value = sector_data[metric].median()

    median_values.append(
        {
            "Metric": metric,
            "Median": value,
        }
    )

median_df = pd.DataFrame(median_values)

median_df["Median"] = pd.to_numeric(
    median_df["Median"],
    errors="coerce"
)

median_chart_df = median_df.dropna(
    subset=["Median"]
)

if median_chart_df.empty:

    st.info(
        "Sector KPI data is not available."
    )

else:

    fig_kpi = px.bar(
        median_chart_df,
        x="Metric",
        y="Median",
        text="Median",
        title=f"{selected_sector}: Median Financial KPIs",
    )

    fig_kpi.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside"
    )

    fig_kpi.update_layout(
        xaxis_title="Metric",
        yaxis_title="Median Value",
        height=500,
    )

    st.plotly_chart(
        fig_kpi,
        use_container_width=True
    )


# ---------------------------------------------------------
# COMPANY TABLE
# ---------------------------------------------------------

st.divider()

st.subheader("📋 Companies in Sector")

table_columns = [
    "company_id",
    "company_name",
    "sub_sector",
    "Revenue",
    "ROE",
    "ROCE",
    "Net Profit Margin",
    "Debt / Equity",
    "Revenue CAGR 5yr",
    "PAT CAGR 5yr",
    "Market Cap",
]

table = sector_data[table_columns].copy()

table = table.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "sub_sector": "Sub-Sector",
        "Revenue": "Revenue",
        "ROE": "ROE %",
        "ROCE": "ROCE %",
        "Net Profit Margin": "NPM %",
        "Debt / Equity": "D/E",
        "Revenue CAGR 5yr": "Revenue CAGR %",
        "PAT CAGR 5yr": "PAT CAGR %",
        "Market Cap": "Market Cap ₹ Cr",
    }
)

numeric_columns = table.select_dtypes(
    include="number"
).columns

table[numeric_columns] = table[
    numeric_columns
].round(2)

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True
)

st.caption(
    f"Showing {len(sector_data)} companies "
    f"with available financial data in {selected_sector}."
)