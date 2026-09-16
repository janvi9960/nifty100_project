import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "nifty100.db"
CASHFLOW_PATH = PROJECT_ROOT / "output" / "cashflow_intelligence.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "output"
REPORTS_DIR = PROJECT_ROOT / "reports"

OUTPUT_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)


FEATURES = [
    "return_on_equity",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin",
]


def load_clustering_data():
    """Load latest financial ratios, sector data, and FCF CAGR data."""
    conn = sqlite3.connect(DB_PATH)

    ratios = pd.read_sql_query(
        """
        SELECT *
        FROM financial_ratios
        WHERE year = (
            SELECT MAX(year)
            FROM financial_ratios fr2
            WHERE fr2.company_id = financial_ratios.company_id
        )
        """,
        conn,
    )

    sectors = pd.read_sql_query(
        """
        SELECT company_id, broad_sector
        FROM sectors
        """,
        conn,
    )

    conn.close()

    cashflow = pd.read_excel(CASHFLOW_PATH)[
        ["company_id", "fcf_cagr_5yr"]
    ]

    df = ratios.merge(sectors, on="company_id", how="left")
    df = df.merge(cashflow, on="company_id", how="left", suffixes=("", "_cashflow"))

    if "fcf_cagr_5yr_cashflow" in df.columns:
        df["fcf_cagr_5yr"] = df["fcf_cagr_5yr_cashflow"]
        df.drop(columns=["fcf_cagr_5yr_cashflow"], inplace=True)

    return df


def impute_sector_medians(df):
    """Fill missing clustering features using broad-sector medians."""
    df = df.copy()

    for feature in FEATURES:
        sector_medians = df.groupby("broad_sector")[feature].transform("median")
        df[feature] = df[feature].fillna(sector_medians)
        df[feature] = df[feature].fillna(df[feature].median())

    return df


def generate_elbow_plot(X_scaled):
    """Generate the KMeans elbow plot for k values 2 through 10."""
    inertias = []

    for k in range(2, 11):
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        model.fit(X_scaled)
        inertias.append(model.inertia_)

    plt.figure(figsize=(9, 6))
    plt.plot(range(2, 11), inertias, marker="o")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.title("KMeans Elbow Plot")
    plt.xticks(range(2, 11))
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    path = REPORTS_DIR / "elbow_plot.png"
    plt.savefig(path, dpi=150)
    plt.close()

    print(f"Saved: {path}")


def run_clustering():
    """Run KMeans clustering and save company cluster assignments."""
    df = load_clustering_data()

    print(f"Companies loaded: {df['company_id'].nunique()}")
    print(f"Rows loaded: {len(df)}")

    missing_before = df[FEATURES].isna().sum()
    print("\nMissing values before imputation:")
    print(missing_before)

    df = impute_sector_medians(df)

    missing_after = df[FEATURES].isna().sum()
    print("\nMissing values after imputation:")
    print(missing_after)

    if df["company_id"].nunique() != 92:
        raise ValueError(
            f"Expected 92 companies, found {df['company_id'].nunique()}"
        )

    X = df[FEATURES].copy()

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    generate_elbow_plot(X_scaled)

    model = KMeans(
        n_clusters=5,
        random_state=42,
        n_init=10,
    )

    cluster_ids = model.fit_predict(X_scaled)

    df["cluster_id"] = cluster_ids

    distances = model.transform(X_scaled)
    df["distance_from_centroid"] = distances.min(axis=1)

    cluster_names = {
        0: "High-Quality Compounders",
        1: "Defensive Dividend Payers",
        2: "Value Cyclicals",
        3: "Distressed or Turnaround",
        4: "Emerging Growth",
    }

    df["cluster_name"] = df["cluster_id"].map(cluster_names)

    result = df[
        [
            "company_id",
            "cluster_id",
            "cluster_name",
            "distance_from_centroid",
        ]
    ].sort_values(["cluster_id", "company_id"])

    output_path = OUTPUT_DIR / "cluster_labels.csv"
    result.to_csv(output_path, index=False)

    print(f"\nSaved: {output_path}")
    print(f"Total companies: {len(result)}")
    print("\nCluster counts:")
    print(result["cluster_name"].value_counts().sort_index())

    print("\nCluster sample:")
    print(result.head(15).to_string(index=False))


if __name__ == "__main__":
    run_clustering()
