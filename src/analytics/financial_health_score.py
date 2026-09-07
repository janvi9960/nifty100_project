import sqlite3
from pathlib import Path

import pandas as pd


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "nifty100.db"


def winsorize(series: pd.Series) -> pd.Series:
    """Winsorize values between P10 and P90."""
    numeric = pd.to_numeric(series, errors="coerce")

    valid = numeric.dropna()

    if valid.empty:
        return numeric

    p10 = valid.quantile(0.10)
    p90 = valid.quantile(0.90)

    return numeric.clip(lower=p10, upper=p90)


def normalize_higher_better(series: pd.Series) -> pd.Series:
    """Convert a higher-is-better metric to a 0–100 score."""
    winsorized = winsorize(series)

    valid = winsorized.dropna()

    if valid.empty:
        return winsorized

    low = valid.min()
    high = valid.max()

    if high == low:
        return pd.Series(100.0, index=series.index)

    return ((winsorized - low) / (high - low) * 100).clip(0, 100)


def normalize_lower_better(series: pd.Series) -> pd.Series:
    """Convert a lower-is-better metric to a 0–100 score."""
    winsorized = winsorize(series)

    valid = winsorized.dropna()

    if valid.empty:
        return winsorized

    low = valid.min()
    high = valid.max()

    if high == low:
        return pd.Series(100.0, index=series.index)

    return ((high - winsorized) / (high - low) * 100).clip(0, 100)


def calculate_financial_health_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate the official Financial Health / Composite Quality Score.

    Formula:
        0.30 × ROE_score
      + 0.25 × FCF_score
      + 0.25 × ROCE_score
      + 0.20 × DE_score

    Scores are normalized to 0–100 using P10/P90 winsorisation.
    """

    result = df.copy()

    result["roe_score"] = normalize_higher_better(
        result["return_on_equity"]
    )

    result["fcf_score"] = normalize_higher_better(
        result["free_cash_flow"]
    )

    result["roce_score"] = normalize_higher_better(
        result["return_on_capital"]
    )

    result["de_score"] = normalize_lower_better(
        result["debt_to_equity"]
    )

    result["composite_quality_score"] = (
        0.30 * result["roe_score"]
        + 0.25 * result["fcf_score"]
        + 0.25 * result["roce_score"]
        + 0.20 * result["de_score"]
    ).clip(0, 100).round(2)

    return result


def main():
    print("FINANCIAL HEALTH SCORE")
    print("=" * 60)

    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(
            """
            SELECT
                company_id,
                year,
                return_on_equity,
                free_cash_flow,
                return_on_capital,
                debt_to_equity
            FROM financial_ratios
            """,
            conn,
        )

    print(f"Rows loaded: {len(df)}")

    scored = calculate_financial_health_score(df)

    with sqlite3.connect(DB_PATH) as conn:
        for _, row in scored.iterrows():
            conn.execute(
                """
                UPDATE financial_ratios
                SET composite_quality_score = ?
                WHERE company_id = ?
                  AND year = ?
                """,
                (
                    None
                    if pd.isna(row["composite_quality_score"])
                    else float(row["composite_quality_score"]),
                    row["company_id"],
                    row["year"],
                ),
            )

        conn.commit()

    valid_scores = scored["composite_quality_score"].dropna()

    print(f"Scores calculated: {len(valid_scores)}")

    if not valid_scores.empty:
        print(f"Minimum score: {valid_scores.min():.2f}")
        print(f"Maximum score: {valid_scores.max():.2f}")

    print()
    print("FINANCIAL HEALTH SCORE COMPLETED")


if __name__ == "__main__":
    main()