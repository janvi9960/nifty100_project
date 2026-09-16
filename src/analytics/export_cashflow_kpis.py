import os
import pandas as pd

from src.analytics.cashflow_analysis import (
    calculate_all_cashflow_kpis,
    calculate_cfo_quality_by_company,
)


OUTPUT_DIR = "output"


def export_cashflow_kpis():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Company-year cash-flow KPIs
    kpi_data = calculate_all_cashflow_kpis()
    kpi_df = pd.DataFrame(kpi_data)

    kpi_path = os.path.join(OUTPUT_DIR, "cashflow_kpis.xlsx")
    kpi_df.to_excel(kpi_path, index=False)

    # Company-level 5-year CFO quality
    quality_data = calculate_cfo_quality_by_company()
    quality_df = pd.DataFrame(quality_data)

    quality_path = os.path.join(
        OUTPUT_DIR,
        "cashflow_cfo_quality.csv",
    )
    quality_df.to_csv(quality_path, index=False)

    # Distress signals
    distress_df = kpi_df[
        kpi_df["capital_allocation"] == "Distress Signal"
    ].copy()

    distress_path = os.path.join(
        OUTPUT_DIR,
        "cashflow_distress.csv",
    )
    distress_df.to_csv(distress_path, index=False)

    print("CASH FLOW KPI EXPORT")
    print("=" * 50)
    print(f"Company-year KPI rows: {len(kpi_df)}")
    print(f"CFO quality companies: {len(quality_df)}")
    print(f"Distress signal rows: {len(distress_df)}")
    print()
    print(f"Created: {kpi_path}")
    print(f"Created: {quality_path}")
    print(f"Created: {distress_path}")
    print()
    print("EXPORT COMPLETED")


if __name__ == "__main__":
    export_cashflow_kpis()