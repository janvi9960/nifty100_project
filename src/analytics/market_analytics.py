import sqlite3
import pandas as pd
import numpy as np


DB_PATH = "data/nifty100.db"

# Annual risk-free rate
RISK_FREE_RATE = 0.065


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create SQLite database connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ============================================================
# LOAD STOCK PRICES
# ============================================================

def load_stock_prices(conn):
    """
    Load monthly stock-price data from SQLite.
    """

    query = """
        SELECT
            company_id,
            date,
            close
        FROM stock_prices
        WHERE close IS NOT NULL
        ORDER BY company_id, date
    """

    df = pd.read_sql_query(query, conn)

    if df.empty:
        return df

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["close"] = pd.to_numeric(
        df["close"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["company_id", "date", "close"]
    )

    df = df.sort_values(
        ["company_id", "date"]
    )

    return df


# ============================================================
# LOAD PEER-GROUP BENCHMARKS
# ============================================================

def load_peer_benchmarks(conn):
    """
    Load the designated benchmark company for every peer group.

    Example:
        Private Banks -> HDFCBANK
        IT Services   -> TCS
        Automobiles   -> MARUTI
    """

    query = """
        SELECT
            peer_group_name,
            company_id
        FROM peer_groups
        WHERE is_benchmark = 1
        ORDER BY peer_group_name
    """

    df = pd.read_sql_query(
        query,
        conn
    )

    return df


# ============================================================
# DAILY / PERIOD RETURNS
# ============================================================

def calculate_returns(df):
    """
    Calculate period returns for every company.

    Since the supplied stock_prices data is monthly,
    these are monthly returns.
    """

    df = df.copy()

    df = df.sort_values(
        ["company_id", "date"]
    )

    df["return"] = (
        df.groupby("company_id")["close"]
        .pct_change()
    )

    return df


# ============================================================
# SHARPE RATIO
# ============================================================

def calculate_sharpe_ratio(
    returns,
    risk_free_rate=RISK_FREE_RATE
):
    """
    Calculate annualized Sharpe Ratio.

    Input returns are assumed to be monthly.

    Formula:

        Sharpe =
        (Average Monthly Excess Return
         / Monthly Volatility)
        × sqrt(12)

    Annual risk-free rate is converted to
    an effective monthly rate.
    """

    returns = pd.Series(
        returns,
        dtype="float64"
    ).dropna()

    if len(returns) < 2:
        return None

    volatility = returns.std()

    if volatility == 0 or pd.isna(volatility):
        return None

    # Convert annual risk-free rate to monthly rate
    rf_monthly = (
        (1 + risk_free_rate) ** (1 / 12)
    ) - 1

    excess_returns = (
        returns - rf_monthly
    )

    sharpe = (
        excess_returns.mean()
        / volatility
    ) * np.sqrt(12)

    if pd.isna(sharpe):
        return None

    return float(sharpe)


# ============================================================
# MAXIMUM DRAWDOWN
# ============================================================

def calculate_max_drawdown(prices):
    """
    Calculate maximum drawdown in percentage.

    Formula:

        Drawdown =
        Current Price / Previous Peak - 1

        Maximum Drawdown =
        Minimum Drawdown
    """

    prices = pd.Series(
        prices,
        dtype="float64"
    ).dropna()

    if len(prices) < 2:
        return None

    running_max = prices.cummax()

    drawdown = (
        prices / running_max
    ) - 1

    max_drawdown = drawdown.min() * 100

    if pd.isna(max_drawdown):
        return None

    return float(max_drawdown)


# ============================================================
# BETA
# ============================================================

def calculate_beta(
    stock_returns,
    benchmark_returns
):
    """
    Calculate Beta using covariance / benchmark variance.

    Formula:

        Beta =
        Covariance(Stock, Benchmark)
        --------------------------------
        Variance(Benchmark)

    Returns None when there is insufficient data
    or benchmark variance is zero.
    """

    data = pd.concat(
        [
            pd.Series(
                stock_returns,
                dtype="float64"
            ),
            pd.Series(
                benchmark_returns,
                dtype="float64"
            ),
        ],
        axis=1
    ).dropna()

    if len(data) < 2:
        return None

    stock = data.iloc[:, 0]
    benchmark = data.iloc[:, 1]

    variance = benchmark.var()

    if variance == 0 or pd.isna(variance):
        return None

    covariance = stock.cov(
        benchmark
    )

    if pd.isna(covariance):
        return None

    beta = covariance / variance

    if pd.isna(beta):
        return None

    return float(beta)


# ============================================================
# ALPHA
# ============================================================

def calculate_alpha(
    stock_returns,
    benchmark_returns,
    risk_free_rate=RISK_FREE_RATE
):
    """
    Calculate annualized Jensen's Alpha.

    Formula:

        Alpha =
        Stock Return
        - Risk Free Rate
        - Beta ×
          (Benchmark Return - Risk Free Rate)

    Input returns are assumed to be monthly.
    """

    data = pd.concat(
        [
            pd.Series(
                stock_returns,
                dtype="float64"
            ),
            pd.Series(
                benchmark_returns,
                dtype="float64"
            ),
        ],
        axis=1
    ).dropna()

    if len(data) < 2:
        return None

    stock = data.iloc[:, 0]
    benchmark = data.iloc[:, 1]

    beta = calculate_beta(
        stock,
        benchmark
    )

    if beta is None:
        return None

    # Annualize average monthly returns
    stock_annualized = (
        (1 + stock.mean()) ** 12
    ) - 1

    benchmark_annualized = (
        (1 + benchmark.mean()) ** 12
    ) - 1

    alpha = (
        stock_annualized
        - risk_free_rate
        - beta
        * (
            benchmark_annualized
            - risk_free_rate
        )
    )

    if pd.isna(alpha):
        return None

    return float(alpha * 100)


# ============================================================
# LOAD BENCHMARK RETURN SERIES
# ============================================================

def build_benchmark_returns(
    df,
    benchmark_df
):
    """
    Create benchmark return series for every peer group.

    Each peer group uses its designated benchmark company.
    """

    benchmark_returns = {}

    for _, row in benchmark_df.iterrows():

        peer_group = row["peer_group_name"]
        benchmark_company = row["company_id"]

        benchmark_data = df[
            df["company_id"] == benchmark_company
        ].copy()

        if benchmark_data.empty:
            continue

        benchmark_data = benchmark_data.sort_values(
            "date"
        )

        benchmark_data = benchmark_data[
            ["date", "return"]
        ].dropna()

        benchmark_returns[peer_group] = {
            "company_id": benchmark_company,
            "data": benchmark_data
        }

    return benchmark_returns


# ============================================================
# COMPANY -> PEER GROUP MAPPING
# ============================================================

def build_company_peer_mapping(peer_df):
    """
    Create company -> peer group mapping.
    """

    mapping = {}

    for peer_group, group in peer_df.groupby(
        "peer_group_name"
    ):

        for company_id in group["company_id"]:
            mapping[company_id] = {
                "peer_group": peer_group
            }

    return mapping


# ============================================================
# COMPANY-LEVEL MARKET METRICS
# ============================================================

def calculate_company_metrics(
    df,
    peer_df=None
):
    """
    Calculate market metrics for every company.

    Metrics:

        - Sharpe Ratio
        - Maximum Drawdown
        - Beta
        - Alpha
        - Benchmark Company
        - Peer Group
        - Observation Count
    """

    results = []

    # --------------------------------------------------------
    # Build benchmark information
    # --------------------------------------------------------

    benchmark_returns = {}

    company_peer_mapping = {}

    if peer_df is not None and not peer_df.empty:

        benchmark_returns = build_benchmark_returns(
            df,
            peer_df
        )

        company_peer_mapping = (
            build_company_peer_mapping(
                peer_df
            )
        )

    # --------------------------------------------------------
    # Calculate metrics company by company
    # --------------------------------------------------------

    for company_id, group in df.groupby(
        "company_id"
    ):

        group = group.sort_values(
            "date"
        )

        returns = (
            group["return"]
            .dropna()
        )

        # Basic market metrics
        sharpe = calculate_sharpe_ratio(
            returns
        )

        max_drawdown = calculate_max_drawdown(
            group["close"]
        )

        # Defaults
        peer_group = None
        benchmark_company = None
        beta = None
        alpha = None

        # ----------------------------------------------------
        # Benchmark calculations
        # ----------------------------------------------------

        if company_id in company_peer_mapping:

            peer_group = company_peer_mapping[
                company_id
            ]["peer_group"]

            benchmark_info = benchmark_returns.get(
                peer_group
            )

            if benchmark_info is not None:

                benchmark_company = (
                    benchmark_info["company_id"]
                )

                benchmark_data = (
                    benchmark_info["data"]
                )

                # Align stock and benchmark by date
                merged = pd.merge(
                    group[
                        ["date", "return"]
                    ],
                    benchmark_data,
                    on="date",
                    how="inner",
                    suffixes=(
                        "_stock",
                        "_benchmark"
                    )
                ).dropna()

                if len(merged) >= 2:

                    beta = calculate_beta(
                        merged["return_stock"],
                        merged["return_benchmark"]
                    )

                    alpha = calculate_alpha(
                        merged["return_stock"],
                        merged["return_benchmark"]
                    )

        # ----------------------------------------------------
        # Store result
        # ----------------------------------------------------

        results.append(
            {
                "company_id": company_id,
                "peer_group": peer_group,
                "benchmark_company": benchmark_company,
                "observations": len(returns),
                "sharpe_ratio": sharpe,
                "max_drawdown_pct": max_drawdown,
                "beta": beta,
                "alpha_pct": alpha,
            }
        )

    return pd.DataFrame(results)


# ============================================================
# VALIDATION
# ============================================================

def validate_metrics(metrics):
    """
    Validate the generated market analytics output.
    """

    if metrics.empty:
        raise ValueError(
            "No market metrics were calculated."
        )

    expected_columns = [
        "company_id",
        "sharpe_ratio",
        "max_drawdown_pct",
        "beta",
        "alpha_pct",
    ]

    missing_columns = [
        column
        for column in expected_columns
        if column not in metrics.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing columns: {missing_columns}"
        )

    if metrics["company_id"].duplicated().any():
        raise ValueError(
            "Duplicate company_id found in metrics."
        )

    return True


# ============================================================
# SUMMARY
# ============================================================

def print_summary(
    df,
    metrics,
    peer_df
):
    """
    Print market analytics summary.
    """

    print()
    print("=" * 60)
    print("MARKET ANALYTICS SUMMARY")
    print("=" * 60)

    print(
        f"Stock price rows: {len(df)}"
    )

    print(
        f"Companies: "
        f"{df['company_id'].nunique()}"
    )

    print(
        f"Date range: "
        f"{df['date'].min().date()} - "
        f"{df['date'].max().date()}"
    )

    print(
        f"Metrics calculated: "
        f"{len(metrics)} companies"
    )

    if peer_df is not None:

        print(
            f"Peer groups: "
            f"{peer_df['peer_group_name'].nunique()}"
        )

        print(
            f"Benchmark companies: "
            f"{peer_df['company_id'].nunique()}"
        )

    print()

    # Number of companies with each metric
    print("Metric coverage:")

    print(
        f"  Sharpe Ratio : "
        f"{metrics['sharpe_ratio'].notna().sum()}"
    )

    print(
        f"  Max Drawdown : "
        f"{metrics['max_drawdown_pct'].notna().sum()}"
    )

    print(
        f"  Beta         : "
        f"{metrics['beta'].notna().sum()}"
    )

    print(
        f"  Alpha        : "
        f"{metrics['alpha_pct'].notna().sum()}"
    )

    print()


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("MARKET ANALYTICS")
    print("=" * 60)

    conn = get_connection()

    try:

        # ----------------------------------------------------
        # Load stock prices
        # ----------------------------------------------------

        df = load_stock_prices(conn)

        if df.empty:
            print(
                "ERROR: No stock price data found."
            )
            return None

        print(
            f"Stock price rows: {len(df)}"
        )

        print(
            f"Companies: "
            f"{df['company_id'].nunique()}"
        )

        print(
            f"Date range: "
            f"{df['date'].min().date()} - "
            f"{df['date'].max().date()}"
        )

        # ----------------------------------------------------
        # Calculate returns
        # ----------------------------------------------------

        df = calculate_returns(df)

        # ----------------------------------------------------
        # Load peer benchmarks
        # ----------------------------------------------------

        peer_df = load_peer_benchmarks(
            conn
        )

        # ----------------------------------------------------
        # Calculate metrics
        # ----------------------------------------------------

        metrics = calculate_company_metrics(
            df,
            peer_df
        )

        # ----------------------------------------------------
        # Validate
        # ----------------------------------------------------

        validate_metrics(
            metrics
        )

        # ----------------------------------------------------
        # Print results
        # ----------------------------------------------------

        print(
            f"Metrics calculated: "
            f"{len(metrics)} companies"
        )

        print()

        print(
            metrics.head(10).to_string(
                index=False
            )
        )

        # ----------------------------------------------------
        # Summary
        # ----------------------------------------------------

        print_summary(
            df,
            metrics,
            peer_df
        )

        return metrics

    finally:

        conn.close()


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()