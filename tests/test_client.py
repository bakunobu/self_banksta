import pytest
import pandas as pd
from local_csv_client import (
    calculate_compound_interest,
    generate_monthly_payment_schedule,
    calculate_deposit_effect
)

def test_calculate_compound_interest():
    result = calculate_compound_interest(principal=1000, rate=0.05, years=2, compounds_per_year=12)
    assert abs(result["total_amount"] - 1104.94) < 0.01

def test_generate_monthly_payment_schedule():
    df = generate_monthly_payment_schedule(principal=120000, annual_rate=0.06, months=12)
    assert len(df) == 12
    assert "payment_amount" in df.columns
    assert abs(df.iloc[0]["payment_amount"] - 10330.56) < 0.01

def test_calculate_deposit_effect():
    result = calculate_deposit_effect(initial=1000, monthly_deposit=100, annual_rate=0.05, years=5)
    assert result["final_balance"] > 8000  # Should grow significantly