import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_companies, get_ratios, get_valuation


st.title("🔎 Stock Screener")
st.caption("Filter Nifty 100 companies using financial and valuation metrics")


# ---------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("Company data is not available.")
    st.stop()


all_ratios = []

for ticker in companies["company_id"]:
    df = get_ratios(ticker)

    if not df.empty:
        latest = df.sort_values("year").iloc[-1].copy()
        all_ratios.append(latest)


if all_ratios:
    ratios = pd.DataFrame(all_ratios)
else:
    ratios = pd.DataFrame()


if ratios.empty:
    st.warning("Financial ratio data is not available.")
    st.stop()


# ---------------------------------------------------------
# MERGE COMPANY DATA
# ---------------------------------------------------------

data = ratios.merge(
    companies[
        ["company_id", "company_name", "broad_sector", "sub_sector"]
    ],
    on="company_id",
    how="left"
)


# ---------------------------------------------------------
# ADD VALUATION DATA
# ---------------------------------------------------------

valuation_rows = []

for ticker in companies["company_id"]:
    valuation = get_valuation(ticker)

    if not valuation.empty:
        latest = valuation.sort_values("year").iloc[-1]

        valuation_rows.append({
            "company_id": ticker,
            "pe_ratio": latest["pe_ratio"],
            "pb_ratio": latest["pb_ratio"],
            "dividend_yield_pct": latest["dividend_yield_pct"],
        })


valuation_df = pd.DataFrame(valuation_rows)

if not valuation_df.empty:
    data = data.merge(
        valuation_df,
        on="company_id",
        how="left"
    )


# ---------------------------------------------------------
# DEFAULT FILTER VALUES
# ---------------------------------------------------------

defaults = {
    "roe_min": 0.0,
    "de_max": 10.0,
    "fcf_min": -10000.0,
    "revenue_cagr_min": -20.0,
    "pat_cagr_min": -20.0,
    "opm_min": -20.0,
    "pe_max": 100.0,
    "pb_max": 20.0,
    "dividend_min": 0.0,
    "icr_min": 0.0,
}


# ---------------------------------------------------------
# PRESETS
# ---------------------------------------------------------

presets = {
    "Custom": defaults,

    "Quality": {
        "roe_min": 15.0,
        "de_max": 1.0,
        "fcf_min": 0.0,
        "revenue_cagr_min": 8.0,
        "pat_cagr_min": 8.0,
        "opm_min": 10.0,
        "pe_max": 60.0,
        "pb_max": 10.0,
        "dividend_min": 0.0,
        "icr_min": 5.0,
    },

    "Value": {
        "roe_min": 8.0,
        "de_max": 2.0,
        "fcf_min": 0.0,
        "revenue_cagr_min": -10.0,
        "pat_cagr_min": -10.0,
        "opm_min": -10.0,
        "pe_max": 20.0,
        "pb_max": 3.0,
        "dividend_min": 0.0,
        "icr_min": 2.0,
    },

    "Growth": {
        "roe_min": 12.0,
        "de_max": 2.0,
        "fcf_min": -10000.0,
        "revenue_cagr_min": 15.0,
        "pat_cagr_min": 12.0,
        "opm_min": 5.0,
        "pe_max": 100.0,
        "pb_max": 20.0,
        "dividend_min": 0.0,
        "icr_min": 2.0,
    },

    "Dividend": {
        "roe_min": 8.0,
        "de_max": 2.0,
        "fcf_min": 0.0,
        "revenue_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 80.0,
        "pb_max": 15.0,
        "dividend_min": 2.0,
        "icr_min": 2.0,
    },

    "Debt-Free": {
        "roe_min": 8.0,
        "de_max": 0.1,
        "fcf_min": 0.0,
        "revenue_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": 0.0,
        "pe_max": 100.0,
        "pb_max": 20.0,
        "dividend_min": 0.0,
        "icr_min": 0.0,
    },

    "Turnaround": {
        "roe_min": 0.0,
        "de_max": 3.0,
        "fcf_min": -10000.0,
        "revenue_cagr_min": 0.0,
        "pat_cagr_min": 0.0,
        "opm_min": -10.0,
        "pe_max": 100.0,
        "pb_max": 20.0,
        "dividend_min": 0.0,
        "icr_min": 0.0,
    },
}


selected_preset = st.sidebar.selectbox(
    "🎯 Screening Preset",
    list(presets.keys())
)


# ---------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------

st.sidebar.subheader("📊 Financial Filters")

preset = presets[selected_preset]


roe_min = st.sidebar.slider(
    "ROE Minimum (%)",
    -100.0,
    100.0,
    float(preset["roe_min"]),
    1.0
)

de_max = st.sidebar.slider(
    "Debt / Equity Maximum",
    0.0,
    10.0,
    float(preset["de_max"]),
    0.1
)

fcf_min = st.sidebar.slider(
    "FCF Minimum (₹ Cr)",
    -10000.0,
    100000.0,
    float(preset["fcf_min"]),
    100.0
)

revenue_cagr_min = st.sidebar.slider(
    "Revenue CAGR 5yr Minimum (%)",
    -50.0,
    100.0,
    float(preset["revenue_cagr_min"]),
    1.0
)

pat_cagr_min = st.sidebar.slider(
    "PAT CAGR 5yr Minimum (%)",
    -50.0,
    100.0,
    float(preset["pat_cagr_min"]),
    1.0
)

opm_min = st.sidebar.slider(
    "OPM Minimum (%)",
    -100.0,
    100.0,
    float(preset["opm_min"]),
    1.0
)

pe_max = st.sidebar.slider(
    "P/E Maximum",
    0.0,
    200.0,
    float(preset["pe_max"]),
    1.0
)

pb_max = st.sidebar.slider(
    "P/B Maximum",
    0.0,
    50.0,
    float(preset["pb_max"]),
    0.5
)

dividend_min = st.sidebar.slider(
    "Dividend Yield Minimum (%)",
    0.0,
    20.0,
    float(preset["dividend_min"]),
    0.5
)

icr_min = st.sidebar.slider(
    "Interest Coverage Minimum",
    0.0,
    50.0,
    float(preset["icr_min"]),
    0.5
)


# ---------------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------------

filtered = data.copy()


def apply_min_filter(df, column, value):
    if column in df.columns:
        return df[
            df[column].isna() | (df[column] >= value)
        ]
    return df


def apply_max_filter(df, column, value):
    if column in df.columns:
        return df[
            df[column].isna() | (df[column] <= value)
        ]
    return df


filtered = apply_min_filter(
    filtered,
    "return_on_equity",
    roe_min
)

filtered = apply_max_filter(
    filtered,
    "debt_to_equity",
    de_max
)

filtered = apply_min_filter(
    filtered,
    "free_cash_flow",
    fcf_min
)

filtered = apply_min_filter(
    filtered,
    "revenue_cagr_5yr",
    revenue_cagr_min
)

filtered = apply_min_filter(
    filtered,
    "pat_cagr_5yr",
    pat_cagr_min
)

filtered = apply_min_filter(
    filtered,
    "operating_profit_margin",
    opm_min
)

filtered = apply_max_filter(
    filtered,
    "pe_ratio",
    pe_max
)

filtered = apply_max_filter(
    filtered,
    "pb_ratio",
    pb_max
)

filtered = apply_min_filter(
    filtered,
    "dividend_yield_pct",
    dividend_min
)

filtered = apply_min_filter(
    filtered,
    "interest_coverage",
    icr_min
)


# ---------------------------------------------------------
# RESULT COUNT
# ---------------------------------------------------------

st.subheader("📋 Screening Results")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Companies Found",
        len(filtered)
    )

with col2:
    st.metric(
        "Total Companies",
        len(data)
    )

with col3:
    if len(data) > 0:
        percentage = len(filtered) / len(data) * 100
        st.metric(
            "Match %",
            f"{percentage:.1f}%"
        )
    else:
        st.metric("Match %", "N/A")


# ---------------------------------------------------------
# RESULT TABLE
# ---------------------------------------------------------

display_columns = [
    "company_id",
    "company_name",
    "broad_sector",
    "composite_quality_score",
    "return_on_equity",
    "debt_to_equity",
    "free_cash_flow",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "operating_profit_margin",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield_pct",
    "interest_coverage",
]


available_columns = [
    column
    for column in display_columns
    if column in filtered.columns
]

result_table = filtered[available_columns].copy()

result_table = result_table.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "broad_sector": "Sector",
        "composite_quality_score": "Quality Score",
        "return_on_equity": "ROE %",
        "debt_to_equity": "D/E",
        "free_cash_flow": "FCF ₹ Cr",
        "revenue_cagr_5yr": "Revenue CAGR 5yr %",
        "pat_cagr_5yr": "PAT CAGR 5yr %",
        "operating_profit_margin": "OPM %",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield_pct": "Dividend Yield %",
        "interest_coverage": "Interest Coverage",
    }
)

st.dataframe(
    result_table,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# CSV DOWNLOAD
# ---------------------------------------------------------

csv_data = result_table.to_csv(index=False).encode("utf-8")

st.download_button(
    label="⬇️ Download Results as CSV",
    data=csv_data,
    file_name="nifty100_screener_results.csv",
    mime="text/csv"
)