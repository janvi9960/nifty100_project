def calculate_free_cash_flow(operating_activity, investing_activity):
    """
    Calculate Free Cash Flow.

    Formula:
        Operating Activity + Investing Activity

    Returns:
        None if either input is missing.
        Negative FCF is allowed.
    """
    if operating_activity is None or investing_activity is None:
        return None

    return operating_activity + investing_activity


def calculate_cfo_quality_score(cfo_values, pat_values):
    """
    Calculate the average CFO/PAT ratio.

    Classification:
        > 1.0     -> High Quality
        0.5–1.0   -> Moderate
        < 0.5     -> Accrual Risk

    Returns:
        (average_ratio, classification)
    """

    if len(cfo_values) != len(pat_values):
        raise ValueError("CFO and PAT lists must have the same length")

    if not cfo_values:
        return None, None

    ratios = []

    for cfo, pat in zip(cfo_values, pat_values):
        if cfo is None or pat is None or pat == 0:
            return None, None

        ratios.append(cfo / pat)

    average_ratio = sum(ratios) / len(ratios)

    if average_ratio > 1.0:
        classification = "High Quality"
    elif average_ratio >= 0.5:
        classification = "Moderate"
    else:
        classification = "Accrual Risk"

    return average_ratio, classification


def calculate_capex_intensity(investing_activity, sales):
    """
    Calculate CapEx Intensity.

    Formula:
        abs(Investing Activity) / Sales * 100

    Classification:
        < 3%    -> Asset Light
        3–8%    -> Moderate
        > 8%    -> Capital Intensive

    Returns:
        (percentage, classification)
    """

    if investing_activity is None or sales is None or sales == 0:
        return None, None

    percentage = (abs(investing_activity) / sales) * 100

    if percentage < 3:
        classification = "Asset Light"
    elif percentage <= 8:
        classification = "Moderate"
    else:
        classification = "Capital Intensive"

    return percentage, classification


def calculate_fcf_conversion_rate(free_cash_flow, operating_profit):
    """
    Calculate FCF Conversion Rate.

    Formula:
        FCF / Operating Profit * 100

    Returns:
        None if either input is missing or operating profit is zero.
    """

    if free_cash_flow is None or operating_profit is None:
        return None

    if operating_profit == 0:
        return None

    return (free_cash_flow / operating_profit) * 100


def classify_capital_allocation(
    cfo_sign,
    cfi_sign,
    cff_sign,
    cfo_pat_ratio=None,
):
    """
    Classify capital allocation pattern based on
    CFO, CFI and CFF signs.

    Patterns:

        (+, -, -) -> Reinvestor
        (+, -, -) with CFO/PAT > 1 -> Shareholder Returns
        (+, +, -) -> Liquidating Assets
        (-, +, +) -> Distress Signal
        (-, -, +) -> Growth Funded by Debt
        (+, +, +) -> Cash Accumulator
        (-, -, -) -> Pre-Revenue
        (+, -, +) -> Mixed
    """

    pattern = (cfo_sign, cfi_sign, cff_sign)

    if pattern == ("+", "-", "-"):
        if cfo_pat_ratio is not None and cfo_pat_ratio > 1.0:
            return "Shareholder Returns"

        return "Reinvestor"

    if pattern == ("+", "+", "-"):
        return "Liquidating Assets"

    if pattern == ("-", "+", "+"):
        return "Distress Signal"

    if pattern == ("-", "-", "+"):
        return "Growth Funded by Debt"

    if pattern == ("+", "+", "+"):
        return "Cash Accumulator"

    if pattern == ("-", "-", "-"):
        return "Pre-Revenue"

    if pattern == ("+", "-", "+"):
        return "Mixed"

    return "Unknown"


def detect_distress_signal(cfo, cff):
    """
    Detect a separate distress alert.

    Distress condition:
        CFO < 0 AND CFF > 0

    This is separate from capital-allocation classification.
    """

    if cfo is None or cff is None:
        return False

    return cfo < 0 and cff > 0


def detect_deleveraging(latest_cff, latest_borrowings, previous_borrowings):
    """
    Detect a deleveraging signal.

    Deleveraging condition:
        Latest CFF < 0
        AND latest borrowings < previous-year borrowings
    """

    if (
        latest_cff is None
        or latest_borrowings is None
        or previous_borrowings is None
    ):
        return False

    return (
        latest_cff < 0
        and latest_borrowings < previous_borrowings
    )