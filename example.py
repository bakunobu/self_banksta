from utils import calculate_compound_interest, generate_monthly_payment_schedule, calculate_deposit_effect

print(calculate_compound_interest(45_000, 6))

print(calculate_compound_interest(45_000, 12, .18))

print(generate_monthly_payment_schedule(45_000, 12, .18))

print(calculate_deposit_effect(5500, 6, .18))