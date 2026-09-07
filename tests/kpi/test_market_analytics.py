from src.analytics.market_analytics import (
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_beta,
    calculate_alpha,
)


def test_max_drawdown():
    prices = [100, 120, 90, 110]

    result = calculate_max_drawdown(prices)

    assert round(result, 2) == -25.00


def test_max_drawdown_no_decline():
    prices = [100, 110, 120, 130]

    result = calculate_max_drawdown(prices)

    assert round(result, 2) == 0.00


def test_sharpe_ratio_insufficient_data():
    result = calculate_sharpe_ratio([0.01])

    assert result is None


def test_sharpe_ratio_zero_volatility():
    result = calculate_sharpe_ratio(
        [0.01, 0.01, 0.01]
    )

    assert result is None


def test_beta_normal():
    stock_returns = [0.01, 0.02, 0.03, 0.04]
    benchmark_returns = [0.01, 0.02, 0.03, 0.04]

    result = calculate_beta(
        stock_returns,
        benchmark_returns
    )

    assert round(result, 2) == 1.00


def test_beta_insufficient_data():
    result = calculate_beta(
        [0.01],
        [0.02]
    )

    assert result is None


def test_alpha_insufficient_data():
    result = calculate_alpha(
        [0.01],
        [0.02]
    )

    assert result is None
def test_beta_with_perfect_positive_relationship():
    stock_returns = [0.01, 0.02, 0.03, 0.04]
    benchmark_returns = [0.01, 0.02, 0.03, 0.04]

    result = calculate_beta(
        stock_returns,
        benchmark_returns
    )

    assert round(result, 2) == 1.00


def test_alpha_returns_value():
    stock_returns = [0.02, 0.03, 0.04, 0.05]
    benchmark_returns = [0.01, 0.02, 0.03, 0.04]

    result = calculate_alpha(
        stock_returns,
        benchmark_returns
    )

    assert result is not None