def calculate_monthly_payment(principal, annual_interest_rate, period_years):
    """
    Calculate monthly payment for a loan with daily compounded interest.
    
    Args:
        principal (float): The initial loan amount
        annual_interest_rate (float): Annual interest rate (as decimal, e.g. 0.05 for 5%)
        period_years (float): Loan period in years
    
    Returns:
        float: Monthly payment amount
    """
    
    # Convert annual rate to daily rate
    daily_rate = annual_interest_rate / 365
    
    # Total number of days in the loan period
    total_days = period_years * 365
    
    # For daily compounding with monthly payments, we need to calculate
    # the effective monthly interest rate based on daily compounding
    daily_growth_factor = (1 + daily_rate)
    monthly_growth_factor = daily_growth_factor ** 30  # Approximate month length
    effective_monthly_rate = monthly_growth_factor - 1
    
    # Total number of monthly payments
    num_payments = period_years * 12
    
    # Standard loan payment formula using the effective monthly rate
    if effective_monthly_rate > 0:
        monthly_payment = principal * (effective_monthly_rate * (1 + effective_monthly_rate) ** num_payments) / \
                        ((1 + effective_monthly_rate) ** num_payments - 1)
    else:
        # Handle zero interest case
        monthly_payment = principal / num_payments
    
    return monthly_payment


# Example usage
if __name__ == "__main__":
    # Example parameters
    principal = 10000  # $10,000 loan
    annual_interest_rate = 0.05  # 5% annual interest
    period_years = 5  # 5 year loan
    
    monthly_payment = calculate_monthly_payment(principal, annual_interest_rate, period_years)
    
    print(f"Loan Details:")
    print(f"Principal: ${principal:,.2f}")
    print(f"Annual Interest Rate: {annual_interest_rate:.1%}")
    print(f"Period: {period_years} years")
    print(f"Monthly Payment: ${monthly_payment:.2f}")
    
    # Calculate total paid and interest paid
    total_paid = monthly_payment * period_years * 12
    total_interest = total_paid - principal
    print(f"Total Paid: ${total_paid:,.2f}")
    print(f"Total Interest: ${total_interest:,.2f}")