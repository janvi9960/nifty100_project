import pytest

from src.analytics.ratios import (
    calculate_net_profit_margin,
    calculate_operating_profit_margin,
    calculate_roe,
    calculate_roce,
    calculate_roa,
    check_opm_mismatch,
)


def test_net_profit_margin_normal():
    assert calculate_net_profit_margin(100, 1000) == pytest.approx(10.0)


def test_net_profit_margin_zero_sales():
    assert calculate_net_profit_margin(100, 0) is None


def test_roe_normal():
    assert calculate_roe(100, 500, 500) == pytest.approx(10.0)


def test_roe_negative_equity():
    assert calculate_roe(100, -600, 500) is None


def test_roce_normal():
    assert calculate_roce(200, 500, 300, 200) == pytest.approx(20.0)


def test_roa_normal():
    assert calculate_roa(100, 1000) == pytest.approx(10.0)


def test_roa_zero_assets():
    assert calculate_roa(100, 0) is None


def test_opm_crosscheck_mismatch():
    assert check_opm_mismatch(15.0, 12.0) is True