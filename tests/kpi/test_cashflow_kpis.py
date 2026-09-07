import pytest

from src.analytics.cashflow_kpis import (
    calculate_free_cash_flow,
    calculate_cfo_quality_score,
    calculate_capex_intensity,
    calculate_fcf_conversion_rate,
    classify_capital_allocation,
)


def test_free_cash_flow():
    assert calculate_free_cash_flow(500, -200) == 300


def test_negative_free_cash_flow():
    assert calculate_free_cash_flow(200, -500) == -300


def test_cfo_quality_high():
    score, label = calculate_cfo_quality_score(
        [120, 110, 130, 115, 125],
        [100, 100, 100, 100, 100],
    )
    assert score == pytest.approx(1.2)
    assert label == "High Quality"


def test_cfo_quality_moderate():
    score, label = calculate_cfo_quality_score(
        [70, 60, 80, 65, 75],
        [100, 100, 100, 100, 100],
    )
    assert score == pytest.approx(0.7)
    assert label == "Moderate"


def test_cfo_quality_accrual_risk():
    score, label = calculate_cfo_quality_score(
        [30, 40, 35, 25, 45],
        [100, 100, 100, 100, 100],
    )
    assert score == pytest.approx(0.35)
    assert label == "Accrual Risk"


def test_cfo_quality_zero_pat():
    score, label = calculate_cfo_quality_score(
        [100, 100, 100, 100, 100],
        [100, 100, 0, 100, 100],
    )
    assert score is None
    assert label is None


def test_capex_intensity_asset_light():
    percentage, label = calculate_capex_intensity(-20, 1000)
    assert percentage == pytest.approx(2.0)
    assert label == "Asset Light"


def test_capex_intensity_moderate():
    percentage, label = calculate_capex_intensity(-50, 1000)
    assert percentage == pytest.approx(5.0)
    assert label == "Moderate"


def test_capex_intensity_capital_intensive():
    percentage, label = calculate_capex_intensity(-150, 1000)
    assert percentage == pytest.approx(15.0)
    assert label == "Capital Intensive"


def test_fcf_conversion_rate():
    assert calculate_fcf_conversion_rate(300, 500) == pytest.approx(60.0)


def test_fcf_conversion_negative():
    assert calculate_fcf_conversion_rate(-200, 500) == pytest.approx(-40.0)


def test_fcf_conversion_zero_operating_profit():
    assert calculate_fcf_conversion_rate(300, 0) is None


def test_reinvestor():
    assert classify_capital_allocation("+", "-", "-") == "Reinvestor"


def test_shareholder_returns():
    assert classify_capital_allocation("+", "-", "-", 1.5) == "Shareholder Returns"


def test_liquidating_assets():
    assert classify_capital_allocation("+", "+", "-") == "Liquidating Assets"


def test_distress_signal():
    assert classify_capital_allocation("-", "+", "+") == "Distress Signal"


def test_growth_funded_by_debt():
    assert classify_capital_allocation("-", "-", "+") == "Growth Funded by Debt"


def test_cash_accumulator():
    assert classify_capital_allocation("+", "+", "+") == "Cash Accumulator"


def test_pre_revenue():
    assert classify_capital_allocation("-", "-", "-") == "Pre-Revenue"


def test_mixed():
    assert classify_capital_allocation("+", "-", "+") == "Mixed"