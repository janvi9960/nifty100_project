import pytest

from src.analytics.ratios import (
    calculate_debt_to_equity,
    check_high_leverage,
    calculate_interest_coverage,
    get_icr_label,
    check_icr_warning,
    calculate_net_debt,
    calculate_asset_turnover,
)


def test_debt_to_equity_normal():
    assert calculate_debt_to_equity(500, 500, 500) == pytest.approx(0.5)


def test_debt_to_equity_debt_free():
    assert calculate_debt_to_equity(0, 500, 500) == 0


def test_debt_to_equity_negative_equity():
    assert calculate_debt_to_equity(500, -600, 500) is None


def test_high_leverage_flag():
    assert check_high_leverage(6, "Industrials") is True


def test_financials_high_leverage_suppressed():
    assert check_high_leverage(10, "Financials") is False


def test_interest_coverage_zero_interest():
    assert calculate_interest_coverage(200, 50, 0) is None


def test_icr_debt_free_label():
    assert get_icr_label(0) == "Debt Free"


def test_icr_warning():
    assert check_icr_warning(1.2) is True