import sqlite3
from pathlib import Path
import pandas as pd

from normaliser import normalize_year, normalize_ticker


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "nifty100.db"


TITLE_ROW_FILES = {
    "companies.xlsx",
    "profitandloss.xlsx",
    "balancesheet.xlsx",
    "cashflow.xlsx",
    "analysis.xlsx",
    "documents.xlsx",
    "prosandcons.xlsx",
}


TABLE_MAP = {
    "companies.xlsx": "companies",
    "profitandloss.xlsx": "profitandloss",
    "balancesheet.xlsx": "balancesheet",
    "cashflow.xlsx": "cashflow",
    "analysis.xlsx": "analysis",
    "documents.xlsx": "documents",
    "prosandcons.xlsx": "prosandcons",
    "sectors.xlsx": "sectors",
    "stock_prices.xlsx": "stock_prices",
    "financial_ratios.xlsx": "financial_ratios",
    "market_cap.xlsx": "market_cap",
    "peer_groups.xlsx": "peer_groups",
}


def read_excel_file(file_path):
    """Read Excel file using the correct header row."""

    if file_path.name in TITLE_ROW_FILES:
        return pd.read_excel(file_path, header=1)

    return pd.read_excel(file_path)


def clean_columns(df):
    """Clean column names."""

    df.columns = [
        str(col).strip().lower().replace(" ", "_")
        for col in df.columns
    ]

    return df


def get_valid_companies(conn):
    """Get company IDs from the master companies table."""

    rows = conn.execute(
        "SELECT id FROM companies"
    ).fetchall()

    return {row[0] for row in rows}


def load_companies(conn):
    """Load companies master table."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "companies.xlsx")
    )

    result = pd.DataFrame({
        "id": df["id"].map(normalize_ticker),
        "company_name": df["company_name"].astype(str).str.strip()
    })

    result = result.dropna(subset=["id"])
    result = result.drop_duplicates(
        subset=["id"],
        keep="first"
    )

    conn.execute("DELETE FROM companies")

    result.to_sql(
        "companies",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def load_profitandloss(conn):
    """Load Profit & Loss data."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "profitandloss.xlsx")
    )

    result = pd.DataFrame({
        "company_id": df["company_id"].map(normalize_ticker),
        "year": df["year"].map(normalize_year),
        "sales": pd.to_numeric(df["sales"], errors="coerce"),
        "operating_profit": pd.to_numeric(
            df["operating_profit"],
            errors="coerce"
        ),
        "net_profit": pd.to_numeric(
            df["net_profit"],
            errors="coerce"
        ),
        "eps": pd.to_numeric(
            df["eps"],
            errors="coerce"
        ),
        "opm_percentage": pd.to_numeric(
            df["opm_percentage"],
            errors="coerce"
        ),
        "dividend_payout_ratio_pct": pd.to_numeric(
            df["dividend_payout"],
            errors="coerce"
        ),
    })

    valid_companies = get_valid_companies(conn)

    # Remove companies not present in master table
    result = result[
        result["company_id"].isin(valid_companies)
    ]

    result = result.dropna(
        subset=["company_id", "year"]
    )

    # Remove duplicate company/year records
    result = result.drop_duplicates(
        subset=["company_id", "year"],
        keep="first"
    )

    conn.execute("DELETE FROM profitandloss")

    result.to_sql(
        "profitandloss",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def load_balancesheet(conn):
    """Load Balance Sheet data."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "balancesheet.xlsx")
    )

    result = pd.DataFrame({
        "company_id": df["company_id"].map(normalize_ticker),
        "year": df["year"].map(normalize_year),
        "borrowings": pd.to_numeric(
            df["borrowings"],
            errors="coerce"
        ),
        "total_assets": pd.to_numeric(
            df["total_assets"],
            errors="coerce"
        ),
        "equity": pd.to_numeric(
            df["equity_capital"],
            errors="coerce"
        ),
        "reserves": pd.to_numeric(
            df["reserves"],
            errors="coerce"
        ),
    })

    valid_companies = get_valid_companies(conn)

    result = result[
        result["company_id"].isin(valid_companies)
    ]

    result = result.dropna(
        subset=["company_id", "year"]
    )

    result = result.drop_duplicates(
        subset=["company_id", "year"],
        keep="first"
    )

    conn.execute("DELETE FROM balancesheet")

    result.to_sql(
        "balancesheet",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def load_cashflow(conn):
    """Load Cash Flow data."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "cashflow.xlsx")
    )

    result = pd.DataFrame({
        "company_id": df["company_id"].map(normalize_ticker),
        "year": df["year"].map(normalize_year),
        "operating_activity": pd.to_numeric(
            df["operating_activity"],
            errors="coerce"
        ),
        "investing_activity": pd.to_numeric(
            df["investing_activity"],
            errors="coerce"
        ),
        "financing_activity": pd.to_numeric(
            df["financing_activity"],
            errors="coerce"
        ),
    })

    valid_companies = get_valid_companies(conn)

    result = result[
        result["company_id"].isin(valid_companies)
    ]

    result = result.dropna(
        subset=["company_id", "year"]
    )

    result = result.drop_duplicates(
        subset=["company_id", "year"],
        keep="first"
    )

    conn.execute("DELETE FROM cashflow")

    result.to_sql(
        "cashflow",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def load_analysis(conn):
    """Load analysis data."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "analysis.xlsx")
    )

    result = pd.DataFrame({
        "company_id": df["company_id"].map(normalize_ticker),
        "analysis_text": df.astype(str).apply(
            lambda row: " | ".join(row.dropna().astype(str)),
            axis=1
        ),
    })

    valid_companies = get_valid_companies(conn)

    result = result[
        result["company_id"].isin(valid_companies)
    ]

    result = result.dropna(
        subset=["company_id"]
    )

    result = result.drop_duplicates(
        subset=["company_id"],
        keep="first"
    )

    conn.execute("DELETE FROM analysis")

    result.to_sql(
        "analysis",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def load_documents(conn):
    """Load documents data."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "documents.xlsx")
    )

    result = pd.DataFrame({
        "company_id": df["company_id"].map(normalize_ticker),
        "year": df["year"].map(normalize_year),
        "document_url": df["annual_report"],
    })

    valid_companies = get_valid_companies(conn)

    result = result[
        result["company_id"].isin(valid_companies)
    ]

    result = result.dropna(
        subset=["company_id"]
    )

    conn.execute("DELETE FROM documents")

    result.to_sql(
        "documents",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def load_prosandcons(conn):
    """Load Pros and Cons data."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "prosandcons.xlsx")
    )

    result = pd.DataFrame({
        "company_id": df["company_id"].map(normalize_ticker),
        "pros": df["pros"],
        "cons": df["cons"],
    })

    valid_companies = get_valid_companies(conn)

    result = result[
        result["company_id"].isin(valid_companies)
    ]

    result = result.dropna(
        subset=["company_id"]
    )

    result = result.drop_duplicates(
        subset=["company_id"],
        keep="first"
    )

    conn.execute("DELETE FROM prosandcons")

    result.to_sql(
        "prosandcons",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def load_sectors(conn):
    """Load sectors data."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "sectors.xlsx")
    )

    result = pd.DataFrame({
        "company_id": df["company_id"].map(normalize_ticker),
        "broad_sector": df["broad_sector"],
        "sub_sector": df["sub_sector"],
    })

    valid_companies = get_valid_companies(conn)

    result = result[
        result["company_id"].isin(valid_companies)
    ]

    result = result.dropna(
        subset=["company_id"]
    )

    result = result.drop_duplicates(
        subset=["company_id"],
        keep="first"
    )

    conn.execute("DELETE FROM sectors")

    result.to_sql(
        "sectors",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def load_stock_prices(conn):
    """Load stock prices."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "stock_prices.xlsx")
    )

    result = pd.DataFrame({
        "company_id": df["company_id"].map(normalize_ticker),
        "date": pd.to_datetime(
            df["date"],
            errors="coerce"
        ).dt.strftime("%Y-%m-%d"),
        "open": pd.to_numeric(
            df["open_price"],
            errors="coerce"
        ),
        "high": pd.to_numeric(
            df["high_price"],
            errors="coerce"
        ),
        "low": pd.to_numeric(
            df["low_price"],
            errors="coerce"
        ),
        "close": pd.to_numeric(
            df["close_price"],
            errors="coerce"
        ),
        "volume": pd.to_numeric(
            df["volume"],
            errors="coerce"
        ),
    })

    valid_companies = get_valid_companies(conn)

    result = result[
        result["company_id"].isin(valid_companies)
    ]

    result = result.dropna(
        subset=["company_id", "date"]
    )

    result = result.drop_duplicates(
        subset=["company_id", "date"],
        keep="first"
    )

    conn.execute("DELETE FROM stock_prices")

    result.to_sql(
        "stock_prices",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def load_financial_ratios(conn):
    """Load financial ratios."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "financial_ratios.xlsx")
    )

    result = pd.DataFrame({
        "company_id": df["company_id"].map(normalize_ticker),
        "year": df["year"].map(normalize_year),
        "net_profit_margin": pd.to_numeric(
            df["net_profit_margin_pct"],
            errors="coerce"
        ),
        "operating_profit_margin": pd.to_numeric(
            df["operating_profit_margin_pct"],
            errors="coerce"
        ),
        "return_on_equity": pd.to_numeric(
            df["return_on_equity_pct"],
            errors="coerce"
        ),
        "return_on_capital": None,
        "debt_to_equity": pd.to_numeric(
            df["debt_to_equity"],
            errors="coerce"
        ),
        "interest_coverage": pd.to_numeric(
            df["interest_coverage"],
            errors="coerce"
        ),
        "free_cash_flow": pd.to_numeric(
            df["free_cash_flow_cr"],
            errors="coerce"
        ),
        "revenue_cagr": None,
        "pat_cagr": None,
        "eps_cagr": None,
        "asset_turnover": pd.to_numeric(
            df["asset_turnover"],
            errors="coerce"
        ),
    })

    valid_companies = get_valid_companies(conn)

    result = result[
        result["company_id"].isin(valid_companies)
    ]

    result = result.dropna(
        subset=["company_id", "year"]
    )

    result = result.drop_duplicates(
        subset=["company_id", "year"],
        keep="first"
    )

    conn.execute("DELETE FROM financial_ratios")

    result.to_sql(
        "financial_ratios",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def load_market_cap(conn):
    """Load market cap."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "market_cap.xlsx")
    )

    result = df[
        [
            "id",
            "company_id",
            "year",
            "market_cap_crore",
            "enterprise_value_crore",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct",
        ]
    ].copy()

    result["company_id"] = result["company_id"].map(
        normalize_ticker
    )

    result["year"] = result["year"].map(
        normalize_year
    )

    valid_companies = get_valid_companies(conn)

    result = result[
        result["company_id"].isin(valid_companies)
    ]

    result = result.dropna(
        subset=["company_id", "year"]
    )

    result = result.drop_duplicates(
        subset=["id"],
        keep="first"
    )

    conn.execute("DELETE FROM market_cap")

    result.to_sql(
        "market_cap",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def load_peer_groups(conn):
    """Load peer groups."""

    df = clean_columns(
        read_excel_file(DATA_DIR / "peer_groups.xlsx")
    )

    result = df[
        [
            "id",
            "peer_group_name",
            "company_id",
            "is_benchmark",
        ]
    ].copy()

    result["company_id"] = result["company_id"].map(
        normalize_ticker
    )

    valid_companies = get_valid_companies(conn)

    result = result[
        result["company_id"].isin(valid_companies)
    ]

    result = result.dropna(
        subset=["company_id"]
    )

    conn.execute("DELETE FROM peer_groups")

    result.to_sql(
        "peer_groups",
        conn,
        if_exists="append",
        index=False
    )

    return len(result)


def main():

    conn = sqlite3.connect(DB_PATH)

    conn.execute("PRAGMA foreign_keys = ON")

    audit = []

    loaders = [
        ("companies.xlsx", "companies", load_companies),
        ("profitandloss.xlsx", "profitandloss", load_profitandloss),
        ("balancesheet.xlsx", "balancesheet", load_balancesheet),
        ("cashflow.xlsx", "cashflow", load_cashflow),
        ("analysis.xlsx", "analysis", load_analysis),
        ("documents.xlsx", "documents", load_documents),
        ("prosandcons.xlsx", "prosandcons", load_prosandcons),
        ("sectors.xlsx", "sectors", load_sectors),
        ("stock_prices.xlsx", "stock_prices", load_stock_prices),
        ("financial_ratios.xlsx", "financial_ratios", load_financial_ratios),
        ("market_cap.xlsx", "market_cap", load_market_cap),
        ("peer_groups.xlsx", "peer_groups", load_peer_groups),
    ]

    try:

        for file_name, table_name, loader_function in loaders:

            print(
                f"\nLoading {file_name} -> {table_name}"
            )

            try:

                row_count = loader_function(conn)

                conn.commit()

                print(
                    f"SUCCESS: {row_count} rows"
                )

                audit.append({
                    "file": file_name,
                    "table": table_name,
                    "rows_loaded": row_count,
                    "status": "SUCCESS",
                })

            except Exception as e:

                conn.rollback()

                print(
                    f"FAILED: {repr(e)}"
                )

                audit.append({
                    "file": file_name,
                    "table": table_name,
                    "rows_loaded": 0,
                    "status": f"FAILED: {repr(e)}",
                })

        # Foreign key check
        fk_errors = conn.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        print(
            f"\nForeign key errors: {len(fk_errors)}"
        )

    finally:

        conn.close()

    output_dir = BASE_DIR / "output"
    output_dir.mkdir(exist_ok=True)

    audit_df = pd.DataFrame(audit)

    audit_path = output_dir / "load_audit.csv"

    audit_df.to_csv(
        audit_path,
        index=False
    )

    print(
        "\nLoad audit created:"
    )

    print(audit_path)


if __name__ == "__main__":
    main()