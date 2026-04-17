import os
import json
import pandas as pd
import datetime as dt

from interest_calculator import InterestRateCalculator, calculate_monthly_payment

from cb_parser import ParseKeyRates

data_path = os.path.join(
    os.path.dirname(__file__), "data", "config.json"
)

def load_config(data_path:str):
    if os.path.exists(data_path):
        with open(data_path, "r") as file_path:
            return json.load(file_path)
        
def update_config(data_path:str, config:dict) -> None:
    if os.path.exists(data_path):
        with open(data_path, "w") as file_path:
            json.dump(config, file_path)
            
CONFIG = {
    'id':'bakunobu',
    'credit_limit':50_000,
    'bank_spread': .03
}

update_config(data_path, CONFIG)

# ... [imports and config remain unchanged] ...

def calculate_compound_interest(principal: float, duration_months: int, annual_rate: float) -> dict:
    """
    Calculate compound interest and monthly payment using correct amortization formula.

    Args:
        principal (float): The initial principal amount
        duration_months (int): The duration of the investment/loan in months
        annual_rate (float): The annual interest rate as a decimal (e.g., 0.05 for 5%)

    Returns:
        dict: A dictionary containing principal, duration in months, rate,
              monthly payment, total paid, and total interest
    """
    # Convert annual rate to monthly rate
    monthly_rate = annual_rate / 12

    # Calculate monthly payment using correct amortization formula
    if monthly_rate > 0:
        num = monthly_rate * (1 + monthly_rate) ** duration_months
        den = (1 + monthly_rate) ** duration_months - 1
        monthly_payment = principal * (num / den)
    else:
        monthly_payment = principal / duration_months

    # Round to 2 decimal places
    monthly_payment = round(monthly_payment, 2)

    # Calculate total amount paid and total interest
    total_paid = monthly_payment * duration_months
    total_interest = total_paid - principal

    return {
        "principal": principal,
        "duration_months": duration_months,
        "annual_rate": annual_rate,
        "monthly_payment": monthly_payment,
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2)
    }
    
def generate_monthly_payment_schedule(
    principal:float,
    duration_months:int,
    annual_rate:float,
    start_date:str=None) -> pd.DataFrame:
    """
    Generate a monthly payment schedule with dates and amounts.

    Args:
        principal (float): Loan amount
        duration_months (int): Number of months
        annual_rate (float): Annual interest rate (e.g., 0.17 for 17%)
        start_date (str): Start date in 'YYYY-MM-DD' format. Defaults to today.

    Returns:
        pd.DataFrame: Columns = ['payment_number', 'payment_date', 'payment_amount']
    """
    # Set start date
    if start_date is None:
        start_date = dt.datetime.today().replace(day=1)  # First day of current month
    else:
        start_date = dt.datetime.strptime(start_date, "%Y-%m-%d").replace(day=1)


    # Generate payment dates (one per month)
    calc = calculate_compound_interest(
        principal,
        duration_months,
        annual_rate
        )
    
    monthly_payment = calc.get('monthly_payment')
    
    dates = [(start_date + pd.DateOffset(months=i)).date() for i in range(duration_months)]

    # Create DataFrame
    schedule = pd.DataFrame({
        'payment_number': range(1, duration_months + 1),
        'payment_date': dates,
        'payment_amount': monthly_payment
    })

    return schedule

def calculate_deposit_effect(
    principal:float,
    num_months:int,
    annual_rate:float) -> float:
    """
    Calculates an effect of deposit (use monthly payments as a principal) over a period of time.
    """
    
    
    total = 0
    
    for i in range(num_months):
        total += calculate_compound_interest(
            principal,
            i+1,
            annual_rate
        )['total_interest']
    return total
    
    

result = calculate_compound_interest(
    50_000,
    6,
    .18
)
print(result)
print(calculate_deposit_effect(result["monthly_payment"], 5, .13))
print(generate_monthly_payment_schedule(500_000, 6, .17, '2026-05-21').to_string())