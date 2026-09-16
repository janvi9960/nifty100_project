import re
import pandas as pd


def normalize_year(value):
    """
    Convert different year formats into a four-digit year.

    Examples:
        2024       -> 2024
        "Dec 2012" -> 2012
        "FY24"     -> 2024
        "FY2024"   -> 2024
        "2023-24"  -> 2024
        "2021/22"  -> 2022
    """

    if pd.isna(value):
        return None

    text = str(value).strip().upper()

    # FY2024 or FY 2024
    match = re.fullmatch(r"FY\s*(20\d{2})", text)
    if match:
        return int(match.group(1))

    # FY24 or FY 24
    match = re.fullmatch(r"FY\s*(\d{2})", text)
    if match:
        return 2000 + int(match.group(1))

    # 2023-24 or 2021/22
    match = re.fullmatch(r"(20\d{2})[-/](\d{2})", text)
    if match:
        start_year = int(match.group(1))
        end_two_digits = int(match.group(2))

        # Convert 23 -> 2023, 24 -> 2024, etc.
        end_year = (start_year // 100) * 100 + end_two_digits

        return end_year

    # Normal four-digit year
    match = re.search(r"\b(19|20)\d{2}\b", text)
    if match:
        return int(match.group())

    return None


def normalize_ticker(value):
    """
    Standardize company ticker/company_id.
    """

    if pd.isna(value):
        return None

    ticker = str(value).strip().upper()

    # Remove spaces
    ticker = re.sub(r"\s+", "", ticker)

    # Known ticker corrections
    ticker_aliases = {
        "AGTL": "ATGL",
    }

    ticker = ticker_aliases.get(ticker, ticker)

    return ticker