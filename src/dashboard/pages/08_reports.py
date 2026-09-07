import sys
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard.utils.db import get_companies


st.title("📄 Annual Reports")
st.caption(
    "Access available annual reports and company documents"
)


# ---------------------------------------------------------
# DATABASE PATH
# ---------------------------------------------------------

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"


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


selected_ticker = (
    selected_company
    .split("(")[-1]
    .replace(")", "")
)


company_row = companies[
    companies["company_id"] == selected_ticker
]


if company_row.empty:
    st.warning("Company not found.")
    st.stop()


company_name = company_row.iloc[0]["company_name"]


st.header(company_name)


# ---------------------------------------------------------
# LOAD REPORTS
# ---------------------------------------------------------

try:

    with sqlite3.connect(DB_PATH) as conn:

        reports = pd.read_sql_query(
            """
            SELECT
                document_id,
                company_id,
                year,
                document_url
            FROM documents
            WHERE company_id = ?
            ORDER BY year DESC
            """,
            conn,
            params=[selected_ticker]
        )

except Exception as error:

    st.error(
        f"Unable to load annual reports: {error}"
    )

    st.stop()


# ---------------------------------------------------------
# NO REPORT DATA
# ---------------------------------------------------------

if reports.empty:

    st.warning(
        f"No annual report records are available for "
        f"{company_name}."
    )

    st.stop()


# ---------------------------------------------------------
# CLEAN REPORT DATA
# ---------------------------------------------------------

reports["year"] = pd.to_numeric(
    reports["year"],
    errors="coerce"
)


reports["document_url"] = (
    reports["document_url"]
    .fillna("")
    .astype(str)
    .str.strip()
)


reports = reports.sort_values(
    "year",
    ascending=False
)


# ---------------------------------------------------------
# AVAILABLE YEARS
# ---------------------------------------------------------

available_years = (
    reports["year"]
    .dropna()
    .astype(int)
    .unique()
    .tolist()
)


st.subheader("📅 Available Annual Reports")


if not available_years:

    st.info(
        "Annual report years are not available."
    )

else:

    st.write(
        f"Reports available for "
        f"{len(available_years)} year(s)."
    )


# ---------------------------------------------------------
# REPORT CARDS
# ---------------------------------------------------------

for _, report in reports.iterrows():

    year = report["year"]
    url = report["document_url"]

    if pd.isna(year):

        year_label = "Year unavailable"

    else:

        year_label = f"FY {int(year)}"


    with st.container(border=True):

        col1, col2, col3 = st.columns(
            [2, 4, 2]
        )


        with col1:

            st.subheader(
                f"📄 {year_label}"
            )


        with col2:

            if url and url.lower().startswith(
                ("http://", "https://")
            ):

                st.markdown(
                    f"**Annual Report**  \n"
                    f"[Open BSE Report ↗]({url})"
                )

            else:

                st.markdown(
                    "**Annual Report**"
                )


        with col3:

            if url and url.lower().startswith(
                ("http://", "https://")
            ):

                st.success(
                    "Report available"
                )

            else:

                st.error(
                    "Report unavailable"
                )


# ---------------------------------------------------------
# REPORT DATA TABLE
# ---------------------------------------------------------

st.divider()

st.subheader("📋 Report Details")


display_reports = reports[
    [
        "document_id",
        "year",
        "document_url"
    ]
].copy()


display_reports = display_reports.rename(
    columns={
        "document_id": "Document ID",
        "year": "Year",
        "document_url": "Report URL",
    }
)


display_reports["Year"] = display_reports[
    "Year"
].apply(
    lambda x: (
        int(x)
        if pd.notna(x)
        else "N/A"
    )
)


display_reports["Report URL"] = (
    display_reports["Report URL"]
    .apply(
        lambda x: (
            x
            if x
            else "N/A"
        )
    )
)


st.dataframe(
    display_reports,
    use_container_width=True,
    hide_index=True
)


# ---------------------------------------------------------
# SUMMARY
# ---------------------------------------------------------

available_count = reports[
    reports["document_url"].str.startswith(
        ("http://", "https://"),
        na=False
    )
].shape[0]


unavailable_count = len(reports) - available_count


st.divider()

col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Report Records",
        len(reports)
    )


with col2:

    st.metric(
        "Reports Available",
        available_count
    )


with col3:

    st.metric(
        "Unavailable",
        unavailable_count
    )


st.caption(
    "Report links are provided from the annual-report "
    "document records available in the project database."
)