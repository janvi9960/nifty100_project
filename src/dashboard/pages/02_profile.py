
import sys
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


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
    get_pl,
    get_bs,
    get_cf,
)


# =========================================================
# DATABASE PATH
# =========================================================

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"


# =========================================================
# PAGE TITLE
# =========================================================

st.title("🏢 Company Profile")
st.caption("Detailed financial profile and historical performance")


# =========================================================
# LOAD COMPANIES
# =========================================================

companies = get_companies()


if companies.empty:
    st.error("Company data is not available.")
    st.stop()


# =========================================================
# COMPANY SEARCH
# =========================================================

company_options = companies.apply(
    lambda row: f"{row['company_name']} ({row['company_id']})",
    axis=1
).tolist()


selected_company_display = st.selectbox(
    "🔎 Search Company",
    company_options
)


# Extract ticker
selected_ticker = (
    selected_company_display
    .split("(")[-1]
    .replace(")", "")
    .strip()
)


# =========================================================
# COMPANY INFORMATION
# =========================================================

company_row = companies[
    companies["company_id"] == selected_ticker
]


if company_row.empty:
    st.warning("Company not found.")
    st.stop()


company = company_row.iloc[0]


company_name = company["company_name"]
broad_sector = company["broad_sector"]
sub_sector = company["sub_sector"]


# =========================================================
# COMPANY HEADER
# =========================================================

st.divider()

st.header(company_name)


info1, info2, info3 = st.columns(3)


with info1:

    st.write("**NSE Ticker**")
    st.write(selected_ticker)


with info2:

    st.write("**Sector**")

    if pd.notna(broad_sector):
        st.write(broad_sector)
    else:
        st.write("N/A")


with info3:

    st.write("**Sub-Sector**")

    if pd.notna(sub_sector):
        st.write(sub_sector)
    else:
        st.write("N/A")


# =========================================================
# ABOUT COMPANY
# =========================================================

st.subheader("📖 About")


def get_about(ticker):

    try:

        with sqlite3.connect(DB_PATH) as conn:

            df = pd.read_sql_query(
                """
                SELECT analysis_text
                FROM analysis
                WHERE TRIM(company_id) = TRIM(?)
                LIMIT 1
                """,
                conn,
                params=[ticker]
            )

        if df.empty:
            return None

        value = df.iloc[0]["analysis_text"]

        if pd.isna(value):
            return None

        value = str(value).strip()

        if not value:
            return None

        return value

    except Exception as e:

        st.error(
            f"Unable to load company information: {e}"
        )

        return None


about_text = get_about(selected_ticker)


if about_text:

    st.info(about_text)

else:

    st.warning(
        f"About information is not available for {selected_ticker}."
    )


# =========================================================
# LOAD FINANCIAL DATA
# =========================================================

ratios = get_ratios(selected_ticker)
pl = get_pl(selected_ticker)
bs = get_bs(selected_ticker)
cf = get_cf(selected_ticker)


# =========================================================
# LATEST AVAILABLE YEAR
# =========================================================

if not ratios.empty:

    ratios = ratios.sort_values("year")

    latest_ratio = ratios.iloc[-1]

    latest_year = latest_ratio["year"]

else:

    latest_ratio = None
    latest_year = None


# =========================================================
# SAFE VALUE FUNCTION
# =========================================================

def safe_value(row, column):

    if row is None:
        return None

    if column not in row.index:
        return None

    value = row[column]

    if pd.isna(value):
        return None

    return value


# =========================================================
# LATEST METRICS
# =========================================================

roe = safe_value(
    latest_ratio,
    "return_on_equity"
)

roce = safe_value(
    latest_ratio,
    "return_on_capital"
)

npm = safe_value(
    latest_ratio,
    "net_profit_margin"
)

debt_equity = safe_value(
    latest_ratio,
    "debt_to_equity"
)

revenue_cagr = safe_value(
    latest_ratio,
    "revenue_cagr_5yr"
)

fcf = safe_value(
    latest_ratio,
    "free_cash_flow"
)


# =========================================================
# FORMATTING FUNCTIONS
# =========================================================

def format_percent(value):

    if value is None:
        return "N/A"

    return f"{value:.2f}%"


def format_number(value):

    if value is None:
        return "N/A"

    return f"{value:,.2f}"


# =========================================================
# SIX KPI TILES
# =========================================================

st.subheader(
    "📊 Key Financial Metrics"
    + (
        f" — {int(latest_year)}"
        if latest_year is not None
        else ""
    )
)


k1, k2, k3 = st.columns(3)


with k1:

    st.metric(
        "ROE",
        format_percent(roe)
    )


with k2:

    st.metric(
        "ROCE",
        format_percent(roce)
    )


with k3:

    st.metric(
        "Net Profit Margin",
        format_percent(npm)
    )


k4, k5, k6 = st.columns(3)


with k4:

    st.metric(
        "Debt / Equity",
        format_number(debt_equity)
    )


with k5:

    st.metric(
        "Revenue CAGR 5yr",
        format_percent(revenue_cagr)
    )


with k6:

    st.metric(
        "Free Cash Flow",
        format_number(fcf)
    )


# =========================================================
# TEN-YEAR REVENUE & NET PROFIT
# =========================================================

st.divider()

st.subheader(
    "📈 Revenue & Net Profit — 10 Year Trend"
)


if not pl.empty:

    financial = pl.copy()

    financial = financial.sort_values(
        "year"
    ).tail(10)


    fig = go.Figure()


    fig.add_bar(
        x=financial["year"],
        y=financial["sales"],
        name="Revenue"
    )


    fig.add_bar(
        x=financial["year"],
        y=financial["net_profit"],
        name="Net Profit"
    )


    fig.update_layout(
        barmode="group",
        xaxis_title="Year",
        yaxis_title="Amount",
        legend_title="Metric",
        hovermode="x unified"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info(
        "Revenue and Net Profit data is not available."
    )


# =========================================================
# ROE / ROCE HISTORICAL TREND
# =========================================================

st.subheader(
    "📊 ROE vs ROCE — Historical Trend"
)


if not ratios.empty:

    trend = ratios.sort_values(
        "year"
    ).copy()


    fig = go.Figure()


    fig.add_trace(
        go.Scatter(
            x=trend["year"],
            y=trend["return_on_equity"],
            mode="lines+markers",
            name="ROE",
            yaxis="y"
        )
    )


    fig.add_trace(
        go.Scatter(
            x=trend["year"],
            y=trend["return_on_capital"],
            mode="lines+markers",
            name="ROCE",
            yaxis="y2"
        )
    )


    fig.update_layout(
        xaxis_title="Year",

        yaxis=dict(
            title="ROE (%)"
        ),

        yaxis2=dict(
            title="ROCE (%)",
            overlaying="y",
            side="right"
        ),

        hovermode="x unified"
    )


    st.plotly_chart(
        fig,
        use_container_width=True
    )

else:

    st.info(
        "ROE and ROCE historical data is not available."
    )


# =========================================================
# PROS & CONS
# =========================================================

st.divider()

st.subheader("👍 Pros & 👎 Cons")


def get_pros_cons(ticker):

    try:

        with sqlite3.connect(DB_PATH) as conn:

            df = pd.read_sql_query(
                """
                SELECT
                    pros,
                    cons
                FROM prosandcons
                WHERE TRIM(company_id) = TRIM(?)
                LIMIT 1
                """,
                conn,
                params=[ticker]
            )


        if df.empty:

            return None, None


        pros_value = df.iloc[0]["pros"]
        cons_value = df.iloc[0]["cons"]


        if pd.isna(pros_value):
            pros_value = None
        else:
            pros_value = str(pros_value).strip()


        if pd.isna(cons_value):
            cons_value = None
        else:
            cons_value = str(cons_value).strip()


        return pros_value, cons_value


    except Exception as e:

        st.error(
            f"Unable to load Pros & Cons: {e}"
        )

        return None, None


pros, cons = get_pros_cons(
    selected_ticker
)


pros_col, cons_col = st.columns(2)


# =========================================================
# PROS
# =========================================================

with pros_col:

    st.markdown("### 👍 Pros")


    if pros:

        st.success(pros)

    else:

        st.info(
            f"No pros information available for {selected_ticker}."
        )


# =========================================================
# CONS
# =========================================================

with cons_col:

    st.markdown("### 👎 Cons")


    if cons:

        st.warning(cons)

    else:

        st.info(
            f"No cons information available for {selected_ticker}."
        )

