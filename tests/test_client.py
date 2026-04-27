import pytest
import requests
import pandas as pd
from local_csv_client import (
    calculate_compound_interest,
    generate_monthly_payment_schedule,
    calculate_deposit_effect,
    ParseKeyRates
)

# --- Existing Tests ---

def test_calculate_compound_interest():
    result = calculate_compound_interest(principal=1000, duration_months=24, annual_rate=0.05)
    assert abs(result["total_paid"] - 1104.94) < 1.00  # Approximate total with monthly payments


def test_generate_monthly_payment_schedule():
    df = generate_monthly_payment_schedule(principal=120000, annual_rate=0.06, duration_months=12)
    assert len(df) == 12
    assert "payment_amount" in df.columns
    assert abs(df.iloc[0]["payment_amount"] - 10330.56) < 0.01


def test_calculate_deposit_effect():
    # Note: This function uses monthly compound interest on growing duration
    result = calculate_deposit_effect(principal=100, num_months=60, annual_rate=0.05)
    assert result > 3000  # Should accumulate significant interest over time


# --- New Test: ParseKeyRates ---
@pytest.mark.integration
def test_parse_key_rate_returns_valid_data():
    """
    Test that ParseKeyRates successfully scrapes the current key rate from CBR website.
    """
    parser = ParseKeyRates()

    try:
        date_str, rate_float = parser.return_actual_rate()
    except Exception as e:
        pytest.fail(f"ParseKeyRates.return_actual_rate() raised an unexpected exception: {e}")

    # Check return types
    assert isinstance(date_str, str), "Date should be a string (e.g., '10.04.2026')"
    assert isinstance(rate_float, float), "Rate should be a float"

    # Validate date format (DD.MM.YYYY)
    assert len(date_str.split('.')) == 3, "Date should be in DD.MM.YYYY format"
    day, month, year = date_str.split('.')
    assert day.isdigit() and 1 <= int(day) <= 31
    assert month.isdigit() and 1 <= int(month) <= 12
    assert year.isdigit() and 2000 <= int(year) <= 2100

    # Validate rate range (CBR key rate is typically between 0% and 30%)
    assert 0.0 <= rate_float <= 30.0, f"Interest rate out of expected range: {rate_float}%"

    # Optional: Log actual value for debugging
    print(f"\n✅ Successfully fetched key rate: {rate_float}% on {date_str}")
    

def test_parse_key_rate_returns_valid_data():
    # Skip if no internet
    try:
        requests.get("https://www.cbr.ru", timeout=3)
    except requests.ConnectionError:
        pytest.skip("No internet connection, skipping live scrape test")

    parser = ParseKeyRates()
    date_str, rate_float = parser.return_actual_rate()

    # ... rest of assertions ...