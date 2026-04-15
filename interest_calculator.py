# interest_calculator.py
from cb_parser import ParseKeyRates
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
        self.key_rate = None

    def update_key_rate(self):
        """Fetch the latest CBR key rate."""
        try:
            self.key_rate = ParseKeyRates().return_actual_rate()[1]
            return True
        except Exception as e:
            print(f"⚠️ Failed to fetch key rate: {e}")
            return False

    @property
    def effective_annual_rate(self) -> float:
        """Total annual interest rate: CBR rate + bank spread."""
        if not self.key_rate:
            raise ValueError("Key rate data not loaded. Call update_key_rate() first.")
        return self.key_rate / 100 + self.bank_spread  # Convert % → decimal

    @property
    def daily_rate(self) -> float:
        """Daily interest rate with daily compounding."""
        # Calculate daily rate that compounds to the effective annual rate
        return (1 + self.effective_annual_rate)**(1/365) - 1

    @property
    def effective_monthly_rate(self) -> float:
        """Monthly compounded rate from daily compounding (avg 30-day month)."""
        # Use the correctly calculated daily rate
        return (1 + self.daily_rate) ** 30 - 1

    def get_rate_summary(self) -> dict:
        """Return full rate breakdown."""
        if not self.key_rate:
            raise ValueError("No key rate data available.")

        return {
            "cbr_key_rate_percent": self.key_rate,  # e.g., 7.5
            "bank_spread_percent": self.bank_spread * 100,
            "effective_annual_rate_percent": self.effective_annual_rate * 100,
            "daily_rate_percent": self.daily_rate * 100,
            "effective_monthly_rate_percent": self.effective_monthly_rate * 100,
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
    if not calculator.key_rate:
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

def calculate_compound_interest(principal: float, duration_months: int, annual_rate: float) -> dict:
    """
    Calculate compound interest with monthly compounding.

    Args:
        principal (float): The initial principal amount
        duration_months (int): The duration of the investment/loan in months
        annual_rate (float): The annual interest rate as a decimal (e.g., 0.05 for 5%)

    Returns:
        dict: A dictionary containing principal, duration in months, rate, 
              monthly payment, total paid, and total interest
    """
    # Convert annual rate to monthly rate
    monthly_rate = (1 + annual_rate) ** (1/12) - 1
    
    # Calculate monthly payment using the loan payment formula
    num_payments = duration_months
    
    if monthly_rate > 0:
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / (((1 + monthly_rate) ** num_payments) - 1)
    else:
        monthly_payment = principal / num_payments
    
    # Calculate total amount paid and total interest
    total_paid = monthly_payment * num_payments
    total_interest = total_paid - principal
    
    return {
        "principal": principal,
        "duration_months": duration_months,
        "annual_rate": annual_rate,
        "monthly_payment": round(monthly_payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2)
    }