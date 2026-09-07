import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# LOAD CAPITAL ALLOCATION DATA
# ---------------------------------------------------------

CAPITAL_FILE = PROJECT_ROOT / "output" / "capital_allocation.csv"

st.title("💰 Capital Allocation")
st.caption(
    "Analyze how Nifty 100 companies allocate cash across "
    "operating, investing and financing activities"
)


if not CAPITAL_FILE.exists():
    st.error(
        "Capital allocation data is not available. "
        "Please run the capital allocation analysis first."
    )
    st.stop()


capital = pd.read_csv(CAPITAL_FILE)


if capital.empty:
    st.warning("Capital allocation data is empty.")
    st.stop()


# ---------------------------------------------------------
# VALIDATE REQUIRED COLUMNS
# ---------------------------------------------------------

required_columns = [
    "company_id",
    "year",
    "cfo_sign",
    "cfi_sign",
    "cff_sign",
    "pattern_label",
]


missing_columns = [
    column
    for column in required_columns
    if column not in capital.columns
]


if missing_columns:
    st.error(
        "Missing columns in capital allocation data: "
        + ", ".join(missing_columns)
    )
    st.stop()


# ---------------------------------------------------------
# CLEAN DATA
# ---------------------------------------------------------

capital["year"] = pd.to_numeric(
    capital["year"],
    errors="coerce"
)

capital["pattern_label"] = (
    capital["pattern_label"]
    .fillna("Unknown")
    .astype(str)
)


# ---------------------------------------------------------
# COMPANY NAMES
# ---------------------------------------------------------

# Load company names directly from SQLite
import sqlite3

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"


with sqlite3.connect(DB_PATH) as conn:
    companies = pd.read_sql_query(
        """
        SELECT id AS company_id, company_name
        FROM companies
        """,
        conn
    )


capital = capital.merge(
    companies,
    on="company_id",
    how="left"
)


capital["company_name"] = capital[
    "company_name"
].fillna(capital["company_id"])


# ---------------------------------------------------------
# LATEST YEAR
# ---------------------------------------------------------

available_years = sorted(
    capital["year"].dropna().unique().astype(int).tolist()
)


if not available_years:
    st.error("No valid years are available.")
    st.stop()


selected_year = st.selectbox(
    "📅 Select Year",
    available_years,
    index=len(available_years) - 1
)


year_data = capital[
    capital["year"] == selected_year
].copy()


if year_data.empty:
    st.warning(
        f"No capital allocation data is available for {selected_year}."
    )
    st.stop()


# ---------------------------------------------------------
# SUMMARY METRICS
# ---------------------------------------------------------

st.subheader(
    f"📊 Capital Allocation Overview — {selected_year}"
)


pattern_count = year_data["pattern_label"].nunique()
company_count = year_data["company_id"].nunique()


col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Companies",
        company_count
    )

with col2:
    st.metric(
        "Allocation Patterns",
        pattern_count
    )

with col3:
    most_common = (
        year_data["pattern_label"]
        .value_counts()
        .index[0]
    )

    st.metric(
        "Most Common Pattern",
        most_common
    )


# ---------------------------------------------------------
# PATTERN COUNTS
# ---------------------------------------------------------

pattern_counts = (
    year_data["pattern_label"]
    .value_counts()
    .reset_index()
)

pattern_counts.columns = [
    "pattern_label",
    "company_count"
]


# ---------------------------------------------------------
# TREEMAP
# ---------------------------------------------------------

st.divider()

st.subheader("🌳 Capital Allocation Patterns")


fig_tree = px.treemap(
    pattern_counts,
    path=["pattern_label"],
    values="company_count",
    title=(
        f"Companies by Capital Allocation Pattern — "
        f"{selected_year}"
    ),
)


fig_tree.update_layout(
    height=650
)


st.plotly_chart(
    fig_tree,
    use_container_width=True
)


# ---------------------------------------------------------
# PATTERN SELECTION
# ---------------------------------------------------------

st.subheader("🔎 Companies by Pattern")


pattern_options = [
    "All Patterns"
] + sorted(
    year_data["pattern_label"].unique().tolist()
)


selected_pattern = st.selectbox(
    "Select Capital Allocation Pattern",
    pattern_options
)


if selected_pattern == "All Patterns":

    selected_data = year_data.copy()

else:

    selected_data = year_data[
        year_data["pattern_label"] == selected_pattern
    ].copy()


# ---------------------------------------------------------
# COMPANY LIST
# ---------------------------------------------------------

display_data = selected_data[
    [
        "company_id",
        "company_name",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label",
    ]
].copy()


display_data = display_data.rename(
    columns={
        "company_id": "Ticker",
        "company_name": "Company",
        "year": "Year",
        "cfo_sign": "CFO Sign",
        "cfi_sign": "CFI Sign",
        "cff_sign": "CFF Sign",
        "pattern_label": "Pattern",
    }
)


st.dataframe(
    display_data,
    use_container_width=True,
    hide_index=True
)


st.caption(
    f"Showing {len(display_data)} companies "
    f"for {selected_year}."
)