import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.etl.normaliser import normalize_year, normalize_ticker


@pytest.mark.parametrize(
    "value, expected",
    [
        (2024, 2024),
        ("2024", 2024),
        ("2020", 2020),
        ("Dec 2012", 2012),
        ("Mar 2014", 2014),
        ("Mar 2015", 2015),
        ("FY24", 2024),
        ("FY 24", 2024),
        ("FY25", 2025),
        ("2023-24", 2024),
        ("2022-23", 2023),
        ("2021/22", 2022),
        ("FY2024", 2024),
        (" 2024 ", 2024),
        ("March 2020", 2020),
        ("December 2021", 2021),
        (None, None),
        ("", None),
        ("Not a year", None),
        ("N/A", None),
    ],
)
def test_normalize_year(value, expected):
    assert normalize_year(value) == expected

@pytest.mark.parametrize(
    "value, expected",
    [
        ("ABB", "ABB"),
        ("abb", "ABB"),
        (" ABB ", "ABB"),
        ("ADANIENT", "ADANIENT"),
        (" adaniensol ", "ADANIENSOL"),
        ("TCS", "TCS"),
        (" tcs ", "TCS"),
        ("HDFCBANK", "HDFCBANK"),
        ("HDFC BANK", "HDFCBANK"),
        ("  RELIANCE  ", "RELIANCE"),
        ("ICICI BANK", "ICICIBANK"),
        ("INFY", "INFY"),
        (" infy ", "INFY"),
        (None, None),
        ("", ""),
    ],
)
def test_normalize_ticker(value, expected):
    assert normalize_ticker(value) == expected