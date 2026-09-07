import pytest

from src.analytics.cagr import calculate_cagr


def test_normal_cagr():
    value, flag = calculate_cagr(100, 150, 3)

    assert value == pytest.approx(14.4714, rel=1e-4)
    assert flag is None


def test_normal_cagr_5_year():
    value, flag = calculate_cagr(100, 200, 5)

    assert value == pytest.approx(14.8698, rel=1e-4)
    assert flag is None


def test_decline_to_loss():
    value, flag = calculate_cagr(100, -50, 3)

    assert value is None
    assert flag == "DECLINE_TO_LOSS"


def test_turnaround():
    value, flag = calculate_cagr(-100, 150, 3)

    assert value is None
    assert flag == "TURNAROUND"


def test_both_negative():
    value, flag = calculate_cagr(-100, -50, 3)

    assert value is None
    assert flag == "BOTH_NEGATIVE"


def test_zero_base():
    value, flag = calculate_cagr(0, 150, 3)

    assert value is None
    assert flag == "ZERO_BASE"


def test_insufficient_data_zero_years():
    value, flag = calculate_cagr(100, 150, 0)

    assert value is None
    assert flag == "INSUFFICIENT"


def test_insufficient_data_negative_years():
    value, flag = calculate_cagr(100, 150, -1)

    assert value is None
    assert flag == "INSUFFICIENT"


def test_one_year_cagr():
    value, flag = calculate_cagr(100, 120, 1)

    assert value == pytest.approx(20.0)
    assert flag is None


def test_cagr_flag_is_none_for_valid_growth():
    value, flag = calculate_cagr(200, 300, 5)

    assert value is not None
    assert flag is None