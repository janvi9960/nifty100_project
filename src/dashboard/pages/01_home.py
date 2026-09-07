import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.express as px


# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================
# DATABASE IMPORTS
# =========================================================

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_valuation,
)


# =========================================================
# PAGE TITLE
# =========================================================

st.title("🏠 Nifty 100 Analytics")
st.subheader("Market Overview")


# =========================================================
# LOAD COMPANIES
# =========================================================

companies = get_companies()


# =========================================================
# LOAD FINANCIAL RATIOS
# =========================================================

all_ratios = []

for ticker in companies["company_id"]:

    df = get_ratios(ticker)

    if not df.empty:
        all_ratios.append(df)


if all_ratios:

    ratios = pd.concat(
        all_ratios,
        ignore_index=True
    )

else:

    ratios = pd.DataFrame()


# =========================================================
# SIDEBAR YEAR SELECTOR
# =========================================================

available_years = list(range(2019, 2025))

selected_year = st.sidebar.selectbox(
    "Select Year",
    available_years,
    index=len(available_years) - 1
)


# =========================================================
# FILTER SELECTED YEAR
# =========================================================

if not ratios.empty:

    year_ratios = ratios[
        ratios["year"] == selected_year
    ].copy()

else:

    year_ratios = pd.DataFrame()


# =========================================================
# KPI 1 — AVERAGE ROE
# =========================================================

if (
    not year_ratios.empty
    and "return_on_equity" in year_ratios.columns
):

    avg_roe = year_ratios[
        "return_on_equity"
    ].mean()

else:

    avg_roe = None


# =========================================================
# KPI 2 — MEDIAN P/E
# =========================================================

pe_values = []

for ticker in companies["company_id"]:

    valuation = get_valuation(ticker)

    if not valuation.empty:

        latest = valuation.iloc[0]

        pe = latest["pe_ratio"]

        if pd.notna(pe) and pe > 0:
            pe_values.append(pe)


if pe_values:

    median_pe = pd.Series(
        pe_values
    ).median()

else:

    median_pe = None


# =========================================================
# KPI 3 — MEDIAN D/E
# =========================================================

if (
    not year_ratios.empty
    and "debt_to_equity" in year_ratios.columns
):

    median_de = year_ratios[
        "debt_to_equity"
    ].median()

else:

    median_de = None


# =========================================================
# KPI 4 — TOTAL COMPANIES
# =========================================================

total_companies = len(companies)


# =========================================================
# KPI 5 — MEDIAN REVENUE CAGR 5YR
# =========================================================

if (
    not year_ratios.empty
    and "revenue_cagr_5yr" in year_ratios.columns
):

    median_revenue_cagr = year_ratios[
        "revenue_cagr_5yr"
    ].median()

else:

    median_revenue_cagr = None


# =========================================================
# KPI 6 — DEBT-FREE COMPANIES
# =========================================================

if (
    not year_ratios.empty
    and "total_debt_cr" in year_ratios.columns
):

    debt_free_count = (
        year_ratios["total_debt_cr"]
        .fillna(0)
        .eq(0)
        .sum()
    )

else:

    debt_free_count = 0


# =========================================================
# KPI TILES — ROW 1
# =========================================================

col1, col2, col3 = st.columns(3)


with col1:

    if avg_roe is not None and pd.notna(avg_roe):

        st.metric(
            "Average ROE",
            f"{avg_roe:.2f}%"
        )

    else:

        st.metric(
            "Average ROE",
            "N/A"
        )


with col2:

    if median_pe is not None and pd.notna(median_pe):

        st.metric(
            "Median P/E",
            f"{median_pe:.2f}"
        )

    else:

        st.metric(
            "Median P/E",
            "N/A"
        )


with col3:

    if median_de is not None and pd.notna(median_de):

        st.metric(
            "Median D/E",
            f"{median_de:.2f}"
        )

    else:

        st.metric(
            "Median D/E",
            "N/A"
        )


# =========================================================
# KPI TILES — ROW 2
# =========================================================

col4, col5, col6 = st.columns(3)


with col4:

    st.metric(
        "Total Companies",
        total_companies
    )


with col5:

    if (
        median_revenue_cagr is not None
        and pd.notna(median_revenue_cagr)
    ):

        st.metric(
            "Median Revenue CAGR 5yr",
            f"{median_revenue_cagr:.2f}%"
        )

    else:

        st.metric(
            "Median Revenue CAGR 5yr",
            "N/A"
        )


with col6:

    st.metric(
        "Debt-Free Companies",
        int(debt_free_count)
    )


# =========================================================
# SEPARATOR
# =========================================================

st.divider()


# =========================================================
# SECTOR DONUT CHART
# =========================================================

st.subheader("🏭 Companies by Sector")


if not year_ratios.empty:

    # Get sectors for companies available in selected year
    sector_data = year_ratios.merge(
        companies[
            [
                "company_id",
                "broad_sector"
            ]
        ],
        on="company_id",
        how="left"
    )

    sector_counts = (
        sector_data[
            "broad_sector"
        ]
        .fillna("Unknown")
        .value_counts()
        .reset_index()
    )

    sector_counts.columns = [
        "sector",
        "company_count"
    ]

else:

    sector_counts = pd.DataFrame(
        columns=[
            "sector",
            "company_count"
        ]
    )


if not sector_counts.empty:

    fig_sector = px.pie(
        sector_counts,
        names="sector",
        values="company_count",
        hole=0.45,
        title=f"Sector Distribution — {selected_year}"
    )

    fig_sector.update_layout(
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        )
    )

    st.plotly_chart(
        fig_sector,
        use_container_width=True
    )

else:

    st.info(
        f"No sector data available for {selected_year}."
    )


# =========================================================
# TOP 5 COMPANIES BY COMPOSITE QUALITY SCORE
# =========================================================

st.subheader(
    "🏆 Top 5 Companies by Composite Quality Score"
)


if (
    not year_ratios.empty
    and "composite_quality_score" in year_ratios.columns
):

    top5 = (
        year_ratios[
            [
                "company_id",
                "composite_quality_score"
            ]
        ]
        .dropna(
            subset=[
                "composite_quality_score"
            ]
        )
        .sort_values(
            "composite_quality_score",
            ascending=False
        )
        .head(5)
    )


    top5 = top5.merge(
        companies[
            [
                "company_id",
                "company_name",
                "broad_sector"
            ]
        ],
        on="company_id",
        how="left"
    )


    top5 = top5[
        [
            "company_id",
            "company_name",
            "broad_sector",
            "composite_quality_score"
        ]
    ]


    # Rename columns for cleaner dashboard display
    top5 = top5.rename(
        columns={
            "company_id": "Ticker",
            "company_name": "Company",
            "broad_sector": "Sector",
            "composite_quality_score": "Composite Quality Score"
        }
    )


    st.dataframe(
        top5,
        use_container_width=True,
        hide_index=True
    )


else:

    st.info(
        "Composite quality score data is not available "
        f"for {selected_year}."
    )

