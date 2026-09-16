import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
CASHFLOW_PATH = PROJECT_ROOT / "output" / "cashflow_intelligence.xlsx"
CLUSTER_LABELS_PATH = PROJECT_ROOT / "output" / "cluster_labels.csv"

OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

OUTPUT_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


CLUSTER_FEATURES = [
    "return_on_equity",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin",
]


CORRELATION_KPIS = [
    "net_profit_margin",
    "operating_profit_margin",
    "return_on_equity",
    "return_on_capital",
    "debt_to_equity",
    "interest_coverage",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "return_on_assets",
]


def load_latest_ratios():
    """Load the latest financial-ratio row for each company."""

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT *
        FROM financial_ratios
        WHERE year = (
            SELECT MAX(year)
            FROM financial_ratios fr2
            WHERE fr2.company_id = financial_ratios.company_id
        )
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


def load_cluster_data():
    """Load ratios, sectors, FCF CAGR, and cluster assignments."""

    ratios = load_latest_ratios()

    conn = sqlite3.connect(DB_PATH)

    sectors = pd.read_sql_query(
        "SELECT company_id, broad_sector FROM sectors",
        conn,
    )

    conn.close()

    cashflow = pd.read_excel(
        CASHFLOW_PATH
    )[["company_id", "fcf_cagr_5yr"]]

    cluster_labels = pd.read_csv(
        CLUSTER_LABELS_PATH
    )[["company_id", "cluster_id", "cluster_name"]]

    df = ratios.merge(
        sectors,
        on="company_id",
        how="left",
    )

    df = df.merge(
        cashflow,
        on="company_id",
        how="left",
    )

    df = df.merge(
        cluster_labels,
        on="company_id",
        how="inner",
    )

    return df


def generate_cluster_profile(df):
    """Generate mean and median statistics for each cluster."""

    profile = (
        df.groupby(
            ["cluster_id", "cluster_name"]
        )[CLUSTER_FEATURES]
        .agg(["mean", "median"])
        .round(2)
    )

    output_path = OUTPUT_DIR / "cluster_profile.csv"

    profile.to_csv(output_path)

    print(f"\nSaved: {output_path}")

    print("\nCluster Profile:")
    print(profile.to_string())


def generate_correlation_heatmap(df):
    """Generate a 10-KPI correlation heatmap."""

    correlation_data = df[CORRELATION_KPIS].copy()

    print("\nMissing values before imputation:")
    print(correlation_data.isna().sum())

    correlation_data = correlation_data.fillna(
        correlation_data.median(numeric_only=True)
    )

    print("\nMissing values after imputation:")
    print(correlation_data.isna().sum())

    correlation_matrix = correlation_data.corr()

    plt.figure(figsize=(12, 9))

    image = plt.imshow(
        correlation_matrix,
        cmap="coolwarm",
        aspect="auto",
        vmin=-1,
        vmax=1,
    )

    plt.colorbar(
        image,
        label="Correlation",
    )

    plt.xticks(
        range(len(correlation_matrix.columns)),
        correlation_matrix.columns,
        rotation=45,
        ha="right",
    )

    plt.yticks(
        range(len(correlation_matrix.index)),
        correlation_matrix.index,
    )

    for i in range(len(correlation_matrix.index)):
        for j in range(len(correlation_matrix.columns)):
            plt.text(
                j,
                i,
                f"{correlation_matrix.iloc[i, j]:.2f}",
                ha="center",
                va="center",
            )

    plt.title(
        "Nifty 100 — Financial KPI Correlation Matrix"
    )

    plt.tight_layout()

    output_path = REPORTS_DIR / "correlation_heatmap.png"

    plt.savefig(
        output_path,
        dpi=150,
    )

    plt.close()

    print(f"\nSaved: {output_path}")


def generate_outlier_report(df):
    """Detect KPI outliers using sector-level Z-scores."""

    outlier_rows = []

    for sector, sector_df in df.groupby("broad_sector"):

        for metric in CORRELATION_KPIS:

            values = sector_df[metric]

            mean = values.mean()
            std = values.std()

            if pd.isna(std) or std == 0:
                continue

            z_scores = (values - mean) / std

            for idx, z_score in z_scores.items():

                if pd.isna(z_score):
                    continue

                if abs(z_score) > 3:

                    outlier_rows.append(
                        {
                            "company_id": df.loc[
                                idx, "company_id"
                            ],
                            "broad_sector": sector,
                            "metric": metric,
                            "value": df.loc[
                                idx, metric
                            ],
                            "z_score": z_score,
                        }
                    )

    outlier_report = pd.DataFrame(
        outlier_rows,
        columns=[
            "company_id",
            "broad_sector",
            "metric",
            "value",
            "z_score",
        ],
    )

    if not outlier_report.empty:

        outlier_report = outlier_report.sort_values(
            "z_score",
            key=lambda x: x.abs(),
            ascending=False,
        )

    output_path = OUTPUT_DIR / "outlier_report.csv"

    outlier_report.to_csv(
        output_path,
        index=False,
    )

    print(f"\nSaved: {output_path}")
    print(
        f"Total outliers: {len(outlier_report)}"
    )


def generate_portfolio_stats(df):
    """Generate portfolio-wide KPI statistics."""

    stats = df[CLUSTER_FEATURES].agg(
        [
            lambda x: x.quantile(0.10),
            lambda x: x.quantile(0.25),
            "median",
            lambda x: x.quantile(0.75),
            lambda x: x.quantile(0.90),
            "mean",
            "std",
        ]
    )

    stats.index = [
        "P10",
        "P25",
        "P50",
        "P75",
        "P90",
        "Mean",
        "Std",
    ]

    stats = stats.T.round(2)

    output_path = OUTPUT_DIR / "portfolio_stats.csv"

    stats.to_csv(output_path)

    print(f"\nSaved: {output_path}")

    print("\nPortfolio Statistics:")
    print(stats.to_string())


def main():

    df = load_cluster_data()

    print(f"Rows loaded: {len(df)}")
    print(
        f"Companies loaded: "
        f"{df['company_id'].nunique()}"
    )
    print(
        f"Latest year: {df['year'].max()}"
    )

    if df["company_id"].nunique() != 92:

        raise ValueError(
            "Expected 92 companies, "
            f"found {df['company_id'].nunique()}"
        )

    generate_cluster_profile(df)

    generate_correlation_heatmap(df)

    generate_outlier_report(df)

    generate_portfolio_stats(df)


if __name__ == "__main__":
    main()