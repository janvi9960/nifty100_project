import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


# Project root:
# nifty100_project/
# ├── data/
# │   └── nifty100.db
# └── src/
#     └── dashboard/
#         └── utils/
#             └── db.py

DB_PATH = Path(__file__).resolve().parents[3] / "data" / "nifty100.db"


def _read_query(query: str, params=None) -> pd.DataFrame:
    """Run a read-only SQLite query and return a DataFrame."""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    """Return company master data with sector information."""
    query = """
        SELECT
            c.id AS company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector
        FROM companies c
        LEFT JOIN sectors s
            ON c.id = s.company_id
        ORDER BY c.company_name
    """
    return _read_query(query)


@st.cache_data(ttl=600)
def get_ratios(ticker: str, year=None) -> pd.DataFrame:
    """Return financial ratios for a company."""
    query = """
        SELECT *
        FROM financial_ratios
        WHERE company_id = ?
    """
    params = [ticker]

    if year is not None:
        query += " AND year = ?"
        params.append(year)

    query += " ORDER BY year"

    return _read_query(query, params)


@st.cache_data(ttl=600)
def get_pl(ticker: str) -> pd.DataFrame:
    """Return profit and loss history."""
    query = """
        SELECT *
        FROM profitandloss
        WHERE company_id = ?
        ORDER BY year
    """
    return _read_query(query, [ticker])


@st.cache_data(ttl=600)
def get_bs(ticker: str) -> pd.DataFrame:
    """Return balance sheet history."""
    query = """
        SELECT *
        FROM balancesheet
        WHERE company_id = ?
        ORDER BY year
    """
    return _read_query(query, [ticker])


@st.cache_data(ttl=600)
def get_cf(ticker: str) -> pd.DataFrame:
    """Return cash flow history."""
    query = """
        SELECT *
        FROM cashflow
        WHERE company_id = ?
        ORDER BY year
    """
    return _read_query(query, [ticker])


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    """Return company sector mapping."""
    query = """
        SELECT
            c.id AS company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector
        FROM companies c
        LEFT JOIN sectors s
            ON c.id = s.company_id
        ORDER BY s.broad_sector, c.company_name
    """
    return _read_query(query)


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    """Return companies belonging to a peer group."""
    query = """
        SELECT
            pg.peer_group_name,
            pg.company_id,
            c.company_name,
            pg.is_benchmark
        FROM peer_groups pg
        LEFT JOIN companies c
            ON pg.company_id = c.id
        WHERE pg.peer_group_name = ?
        ORDER BY pg.is_benchmark DESC, c.company_name
    """
    return _read_query(query, [group_name])


@st.cache_data(ttl=600)
def get_valuation(ticker: str) -> pd.DataFrame:
    """Return latest market valuation data for a company."""
    query = """
        SELECT
            mc.company_id,
            c.company_name,
            mc.year,
            mc.market_cap_crore,
            mc.enterprise_value_crore,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.ev_ebitda,
            mc.dividend_yield_pct
        FROM market_cap mc
        LEFT JOIN companies c
            ON mc.company_id = c.id
        WHERE mc.company_id = ?
        ORDER BY mc.year DESC
    """
    return _read_query(query, [ticker])