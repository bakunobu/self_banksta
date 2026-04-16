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
    monthly_rate = annual_rate / 12
    
    # Calculate monthly payment using the loan payment formula
    
    if monthly_rate > 0:
        monthly_payment = (principal * (1 + monthly_rate) ** duration_months) / duration_months
    else:
        monthly_payment = principal / duration_months
    
    # Calculate total amount paid and total interest
    total_paid = monthly_payment * duration_months
    total_interest = total_paid - principal
    
    return {
        "principal": principal,
        "duration_months": duration_months,
        "annual_rate": annual_rate,
        "monthly_payment": round(monthly_payment, 2),
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

    # # Monthly interest rate
    # monthly_rate = annual_rate / 12

    # # Correct monthly payment using amortization formula
    # if monthly_rate > 0:
    #     monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**duration_months) / \
    #                       (((1 + monthly_rate)**duration_months) - 1)
    # else:
    #     monthly_payment = principal / duration_months

    # monthly_payment = round(monthly_payment, 2)

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

# result = calculate_compound_interest(
#     500_000,
#     6,
#     .17
# )
# print(result)

print(generate_monthly_payment_schedule(500_000, 6, .17, '2026-05-21').to_string())