import pandas as pd

from src.analytics.cashflow_kpis import classify_capital_allocation


def test_reinvestor_pattern():
    assert classify_capital_allocation("+", "-", "-") == "Reinvestor"


def test_shareholder_returns_pattern():
    assert (
        classify_capital_allocation("+", "-", "-", 1.5)
        == "Shareholder Returns"
    )


def test_distress_with_positive_cfi():
    assert (
        classify_capital_allocation("-", "+", "+")
        == "Distress Signal"
    )


def test_growth_funded_by_debt():
    assert (
        classify_capital_allocation("-", "-", "+")
        == "Growth Funded by Debt"
    )


def test_unknown_with_zero_cfi():
    assert (
        classify_capital_allocation("-", "0", "+")
        == "Unknown"
    )


def test_liquidating_assets():
    assert (
        classify_capital_allocation("+", "+", "-")
        == "Liquidating Assets"
    )


def test_cash_accumulator():
    assert (
        classify_capital_allocation("+", "+", "+")
        == "Cash Accumulator"
    )


def test_pre_revenue():
    assert (
        classify_capital_allocation("-", "-", "-")
        == "Pre-Revenue"
    )


def test_mixed():
    assert (
        classify_capital_allocation("+", "-", "+")
        == "Mixed"
    )


def test_capital_allocation_output_exists():
    df = pd.read_csv("output/capital_allocation.csv")

    assert len(df) == 1056
    assert df["company_id"].nunique() == 91
    assert df["pattern_label"].notna().all()