# Make sure the 'dbs' directory exists
import os
from acc import BankAccount

if not os.path.exists("dbs"):
    os.makedirs("dbs")

# Create an account
account = BankAccount(
    client_id="C001",
    interest_rate=0.12,       # 12% annual interest
    credit_limit=5000.00,
    credit_amt=1000.00
)

# Save to database
account.save()

# Modify and save
account.update_credit_amt(1500.00)

# Load into a new instance
account2 = BankAccount(client_id="C001")
if account2.load():
    print(account2)

# Apply interest
account2.apply_monthly_interest()