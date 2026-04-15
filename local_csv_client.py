import os
import json
import pandas as pd

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

result = calculate_compound_interest(
    50_000,
    6,
    .18
)