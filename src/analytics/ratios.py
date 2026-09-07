def calculate_net_profit_margin(net_profit, sales):
    """
    Calculate Net Profit Margin.

    Formula:
        (Net Profit / Sales) * 100

    Returns:
        None if sales is zero.
    """
    if sales == 0:
        return None

    return (net_profit / sales) * 100


def calculate_operating_profit_margin(operating_profit, sales):
    """
    Calculate Operating Profit Margin.

    Formula:
        (Operating Profit / Sales) * 100

    Returns:
        None if sales is zero.
    """
    if sales == 0:
        return None

    return (operating_profit / sales) * 100

def calculate_roe(net_profit, equity, reserves):
    """
    Calculate Return on Equity (ROE).

    Formula:
        (Net Profit / (Equity + Reserves)) * 100

    Returns:
        None if Equity + Reserves <= 0.
    """
    equity_base = equity + reserves

    if equity_base <= 0:
        return None

    return (net_profit / equity_base) * 100

def calculate_roce(ebit, equity_capital, reserves, borrowings):
    """
    Calculate Return on Capital Employed (ROCE).

    Formula:
        EBIT / (Equity + Reserves + Borrowings) * 100

    Returns None when:
        - EBIT is missing
        - Equity is missing
        - Reserves is missing
        - Borrowings is missing
        - Capital employed is zero
    """

    if ebit is None:
        return None

    if equity_capital is None:
        return None

    if reserves is None:
        return None

    if borrowings is None:
        return None

    capital_employed = (
        equity_capital
        + reserves
        + borrowings
    )

    if capital_employed == 0:
        return None

    return (
        ebit / capital_employed
    ) * 100
def calculate_roa(net_profit, total_assets):
    """
    Calculate Return on Assets (ROA).

    Formula:
        (Net Profit / Total Assets) * 100

    Returns:
        None if total assets is zero.
    """
    if total_assets == 0:
        return None

    return (net_profit / total_assets) * 100

def check_opm_mismatch(calculated_opm, source_opm, tolerance=1.0):
    """
    Compare calculated OPM with the source OPM percentage.

    Returns:
        True if the difference is greater than the tolerance.
        False otherwise.

    Returns False when either value is None.
    """
    if calculated_opm is None or source_opm is None:
        return False

    return abs(calculated_opm - source_opm) > tolerance

def calculate_profitability_ratios(
    sales,
    operating_profit,
    net_profit,
    equity,
    reserves,
    borrowings,
    total_assets,
):
    """
    Calculate all profitability ratios for one company-year.

    Returns a dictionary containing:
        net_profit_margin
        operating_profit_margin
        return_on_equity
        return_on_capital
        return_on_assets
    """

    return {
        "net_profit_margin": calculate_net_profit_margin(
            net_profit, sales
        ),
        "operating_profit_margin": calculate_operating_profit_margin(
            operating_profit, sales
        ),
        "return_on_equity": calculate_roe(
            net_profit, equity, reserves
        ),
        "return_on_capital": calculate_roce(
            operating_profit, equity, reserves, borrowings
        ),
        "return_on_assets": calculate_roa(
            net_profit, total_assets
        ),
    }

def calculate_debt_to_equity(borrowings, equity, reserves):
    """
    Calculate Debt-to-Equity ratio.

    Formula:
        Borrowings / (Equity + Reserves)

    Returns:
        0 if borrowings is zero.
        None if equity + reserves <= 0.
    """
    if borrowings == 0:
        return 0

    equity_base = equity + reserves

    if equity_base <= 0:
        return None

    return borrowings / equity_base

def check_high_leverage(debt_to_equity, broad_sector):
    """
    Flag companies with D/E > 5 outside the Financials sector.
    """

    if debt_to_equity is None:
        return False

    if broad_sector == "Financials":
        return False

    return debt_to_equity > 5

def calculate_interest_coverage(operating_profit, other_income, interest):
    """
    Calculate Interest Coverage Ratio.

    Formula:
        (Operating Profit + Other Income) / Interest

    Returns:
        None if interest is zero.
    """
    if interest == 0:
        return None

    return (operating_profit + other_income) / interest

def get_icr_label(interest):
    """
    Return a display label for companies with zero interest expense.
    """
    if interest == 0:
        return "Debt Free"

    return None


def check_icr_warning(interest_coverage):
    """
    Flag companies with ICR below 1.5.
    """
    if interest_coverage is None:
        return False

    return interest_coverage < 1.5

def calculate_net_debt(borrowings, investments):
    """
    Calculate Net Debt.

    Formula:
        Borrowings - Investments

    Investments are treated as a liquid asset proxy.
    """
    return borrowings - investments

def calculate_asset_turnover(sales, total_assets):
    """
    Calculate Asset Turnover.

    Formula:
        Sales / Total Assets

    Returns:
        None if total assets is zero.
    """
    if total_assets == 0:
        return None

    return sales / total_assets
