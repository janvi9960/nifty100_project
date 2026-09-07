import streamlit as st

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

home = st.Page(
    "pages/01_home.py",
    title="Home",
    icon="🏠",
)

profile = st.Page(
    "pages/02_profile.py",
    title="Company Profile",
    icon="🏢",
)

screener = st.Page(
    "pages/03_screener.py",
    title="Screener",
    icon="🔎",
)

peers = st.Page(
    "pages/04_peers.py",
    title="Peers",
    icon="👥",
)

trends = st.Page(
    "pages/05_trends.py",
    title="Trends",
    icon="📈",
)

sectors = st.Page(
    "pages/06_sectors.py",
    title="Sectors",
    icon="🏭",
)

capital = st.Page(
    "pages/07_capital.py",
    title="Capital Allocation",
    icon="💰",
)

reports = st.Page(
    "pages/08_reports.py",
    title="Annual Reports",
    icon="📄",
)

pg = st.navigation(
    [
        home,
        profile,
        screener,
        peers,
        trends,
        sectors,
        capital,
        reports,
    ],
    position="sidebar",
)

pg.run()