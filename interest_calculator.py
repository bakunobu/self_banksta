# interest_calculator.py
from cb_parser import CBRKeyRateParser
from datetime import date


class InterestRateCalculator:
    """
    A class to calculate loan interest rates based on the Central Bank of Russia (CBR) key rate
    plus a fixed bank spread.
    """

    def __init__(self, bank_spread: float = 0.02):
        """
        Args:
            bank_spread (float): Additional margin added by the bank (e.g., 0.02 = 2%)
        """
        self.bank_spread = bank_spread  # in decimal (e.g., 0.02 for 2 pp)
        self.key_rate_data = None

    def update_key_rate(self):
        """Fetch the latest CBR key rate."""
        try:
            self.key_rate_data = CBRKeyRateParser.get_latest_rate()
            return True
        except Exception as e:
            print(f"⚠️ Failed to fetch key rate: {e}")
            return False

    @property
    def effective_annual_rate(self) -> float:
        """Total annual interest rate: CBR rate + bank spread."""
        if not self.key_rate_data:
            raise ValueError("Key rate data not loaded. Call update_key_rate() first.")
        return self.key_rate_data["rate"] / 100 + self.bank_spread  # Convert % → decimal

    @property
    def daily_rate(self) -> float:
        """Daily interest rate with daily compounding."""
        return self.effective_annual_rate / 365

    @property
    def effective_monthly_rate(self) -> float:
        """Monthly compounded rate from daily compounding (avg 30-day month)."""
        return (1 + self.daily_rate) ** 30 - 1

    def get_rate_summary(self) -> dict:
        """Return full rate breakdown."""
        if not self.key_rate_data:
            raise ValueError("No key rate data available.")

        return {
            "cbr_key_rate_percent": self.key_rate_data["rate"],  # e.g., 7.5
            "bank_spread_percent": self.bank_spread * 100,
            "effective_annual_rate_percent": self.effective_annual_rate * 100,
            "daily_rate_percent": self.daily_rate * 100,
            "effective_monthly_rate_percent": self.effective_monthly_rate * 100,
            "rate_as_of_date": self.key_rate_data["date"]
        }


def calculate_monthly_payment(principal: float, period_years: float, calculator: InterestRateCalculator):
    """
    Calculate monthly loan payment using dynamically fetched CBR-based interest rate.

    Args:
        principal: Loan amount
        period_years: Term in years
        calculator: Instance of InterestRateCalculator with updated rate

    Returns:
        dict: Payment details
    """
    if not calculator.key_rate_data:
        raise ValueError("Interest rate data is missing. Update calculator first.")

    num_payments = int(period_years * 12)
    r = calculator.effective_monthly_rate  # Monthly rate

    if r > 0:
        monthly_payment = principal * (r * (1 + r) ** num_payments) / (((1 + r) ** num_payments) - 1)
    else:
        monthly_payment = principal / num_payments

    total_paid = monthly_payment * num_payments
    total_interest = total_paid - principal

    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "num_payments": num_payments,
        "annual_rate": round(calculator.effective_annual_rate * 100, 2)
    }