from pathlib import Path
import sqlite3

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
PEER_FILE = PROJECT_ROOT / "data" / "peer_groups.xlsx"


METRICS = {
    "ROE": "return_on_equity",
    "ROCE": "return_on_capital",
    "NPM": "net_profit_margin",
    "D/E": "debt_to_equity",
    "FCF": "free_cash_flow",
    "PAT CAGR 5yr": "pat_cagr_5yr",
    "Revenue CAGR 5yr": "revenue_cagr_5yr",
    "EPS CAGR 5yr": "eps_cagr_5yr",
    "Interest Coverage": "interest_coverage",
    "Asset Turnover": "asset_turnover",
}


def load_peer_groups():
    """Load company-to-peer-group mapping from peer_groups.xlsx."""

    if not PEER_FILE.exists():
        raise FileNotFoundError(
            f"Peer group file not found: {PEER_FILE}"
        )

    df = pd.read_excel(PEER_FILE)

    print("Peer group columns:", df.columns.tolist())

    return df


def find_column(df, candidates):
    """Find a column using case-insensitive matching."""

    lookup = {
        str(column).strip().lower(): column
        for column in df.columns
    }

    for candidate in candidates:
        key = candidate.strip().lower()

        if key in lookup:
            return lookup[key]

    return None


def prepare_peer_mapping(peer_df):
    """Normalize the peer-group file into company_id + peer_group_name."""

    company_col = find_column(
        peer_df,
        [
            "company_id",
            "company id",
            "id",
            "ticker",
            "symbol",
        ],
    )

    group_col = find_column(
        peer_df,
        [
            "peer_group_name",
            "peer group name",
            "peer_group",
            "peer group",
            "peer_group_id",
            "peer group id",
        ],
    )

    if company_col is None:
        raise ValueError(
            "Could not identify company ID column in peer_groups.xlsx"
        )

    if group_col is None:
        raise ValueError(
            "Could not identify peer group column in peer_groups.xlsx"
        )

    mapping = peer_df[
        [company_col, group_col]
    ].copy()

    mapping.columns = [
        "company_id",
        "peer_group_name",
    ]

    mapping["company_id"] = (
        mapping["company_id"]
        .astype(str)
        .str.strip()
    )

    mapping["peer_group_name"] = (
        mapping["peer_group_name"]
        .astype(str)
        .str.strip()
    )

    mapping = mapping[
        (mapping["company_id"] != "")
        & (mapping["peer_group_name"] != "")
        & (mapping["peer_group_name"].str.lower() != "nan")
    ]

    return mapping.drop_duplicates(
        subset=["company_id"]
    )


def load_ratio_data():
    """Load latest financial-ratio data with company names."""

    query = """
        WITH latest AS (
            SELECT
                fr.*,
                ROW_NUMBER() OVER (
                    PARTITION BY fr.company_id
                    ORDER BY fr.year DESC
                ) AS rn
            FROM financial_ratios fr
        )
        SELECT
            l.company_id,
            c.company_name,
            l.year,
            l.return_on_equity,
            l.return_on_capital,
            l.net_profit_margin,
            l.debt_to_equity,
            l.free_cash_flow,
            l.pat_cagr_5yr,
            l.revenue_cagr_5yr,
            l.eps_cagr_5yr,
            l.interest_coverage,
            l.asset_turnover
        FROM latest l
        JOIN companies c
            ON c.id = l.company_id
        WHERE l.rn = 1
    """

    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)


def calculate_percentile(series, value, inverse=False):
    """
    Calculate percentile rank from 0 to 100.

    Higher-is-better metrics:
        higher value = higher percentile

    Inverse metrics such as D/E:
        lower value = higher percentile
    """

    values = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if pd.isna(value) or len(values) == 0:
        return np.nan

    if inverse:
        value = -float(value)
        values = -values

    rank = (values <= value).sum()

    if len(values) == 1:
        return 100.0

    percentile = (
        (rank - 1) / (len(values) - 1)
    ) * 100

    return round(float(percentile), 2)


def calculate_peer_percentiles():
    print("=" * 60)
    print("NIFTY 100 PEER PERCENTILE ENGINE")
    print("=" * 60)

    peer_df = load_peer_groups()

    print(f"Peer-group rows loaded: {len(peer_df)}")

    mapping = prepare_peer_mapping(peer_df)

    print(f"Companies with peer groups: {len(mapping)}")

    ratio_df = load_ratio_data()

    print(f"Companies with ratio data: {len(ratio_df)}")

    # Convert IDs to strings so the Excel mapping joins safely.
    ratio_df["company_id"] = (
        ratio_df["company_id"]
        .astype(str)
        .str.strip()
    )

    merged = ratio_df.merge(
        mapping,
        on="company_id",
        how="left",
    )

    rows = []

    for peer_group, group in merged.groupby(
        "peer_group_name",
        dropna=True,
    ):
        print(
            f"Processing peer group: "
            f"{peer_group} ({len(group)} companies)"
        )

        for _, company in group.iterrows():

            for metric_name, column in METRICS.items():

                value = company[column]

                # D/E is inverse:
                # lower D/E = better percentile.
                inverse = metric_name == "D/E"

                percentile = calculate_percentile(
                    group[column],
                    value,
                    inverse=inverse,
                )

                rows.append(
                    {
                        "company_id": company["company_id"],
                        "peer_group_name": peer_group,
                        "metric": metric_name,
                        "value": value,
                        "percentile_rank": percentile,
                        "year": company["year"],
                    }
                )

    result = pd.DataFrame(rows)

    print(
        f"\nPercentile rows calculated: {len(result)}"
    )

    return result


def create_table(conn):
    """Create peer_percentiles table."""

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS peer_percentiles (
            company_id TEXT NOT NULL,
            peer_group_name TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL,
            percentile_rank REAL,
            year INTEGER,
            PRIMARY KEY (
                company_id,
                peer_group_name,
                metric,
                year
            )
        )
        """
    )

    conn.commit()


def save_percentiles(result):
    """Save peer percentile results into SQLite."""

    with sqlite3.connect(DB_PATH) as conn:

        create_table(conn)

        # Replace previously generated results.
        conn.execute(
            "DELETE FROM peer_percentiles"
        )

        result.to_sql(
            "peer_percentiles",
            conn,
            if_exists="append",
            index=False,
        )

        conn.commit()

        count = conn.execute(
            "SELECT COUNT(*) FROM peer_percentiles"
        ).fetchone()[0]

    print(
        f"Rows inserted into peer_percentiles: {count}"
    )

    return count


def verify_results():
    """Run basic verification queries."""

    with sqlite3.connect(DB_PATH) as conn:

        total = conn.execute(
            "SELECT COUNT(*) FROM peer_percentiles"
        ).fetchone()[0]

        companies = conn.execute(
            "SELECT COUNT(DISTINCT company_id) "
            "FROM peer_percentiles"
        ).fetchone()[0]

        groups = conn.execute(
            "SELECT COUNT(DISTINCT peer_group_name) "
            "FROM peer_percentiles"
        ).fetchone()[0]

        metrics = conn.execute(
            "SELECT COUNT(DISTINCT metric) "
            "FROM peer_percentiles"
        ).fetchone()[0]

        print("\nVerification")
        print("-" * 40)
        print(f"Total rows:       {total}")
        print(f"Companies ranked: {companies}")
        print(f"Peer groups:      {groups}")
        print(f"Metrics:          {metrics}")


def main():
    result = calculate_peer_percentiles()

    if result.empty:
        print(
            "\nWARNING: No peer percentile rows were generated."
        )
        return

    save_percentiles(result)

    verify_results()

    print("\n" + "=" * 60)
    print("PEER PERCENTILE ENGINE COMPLETED")
    print("=" * 60)


if __name__ == "__main__":
    main()