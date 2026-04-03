import os
from client_credit import Client

# Ensure dbs directory exists
if not os.path.exists("dbs"):
    os.makedirs("dbs")

# Create a client
client = Client(
    client_id="C001",
    name="Alice Johnson",
    email="alice@example.com",
    phone="+1-555-1234"
)

# Add some credit accounts
act1 = client.add_credit_account(
    account_id="ACC001",
    interest_rate=0.12,
    credit_limit=5000.00,
    initial_amount=2000.00
)

act2 = client.add_credit_account(
    account_id="ACC002",
    interest_rate=0.08,
    credit_limit=10000.00,
    initial_amount=5000.00
)

# Apply interest
act1.apply_monthly_interest()

# Close one account (becomes past credit)
act2.close_account()

# Reload client data
client_fresh = Client(client_id="C001", name="", email="")
print("\n--- Client Info ---")
print(client_fresh)
print(f"Total Debt: ${client_fresh.total_outstanding_debt():.2f}")
print("\nActive Accounts:")
for acc in client_fresh.get_active_accounts():
    print(" ", acc)
print("\nClosed Accounts:")
for acc in client_fresh.get_closed_accounts():
    print(" ", acc)
    
    

client = Client(client_id="C001", name="Alice Johnson", email="alice@example.com")

# Make a partial monthly payment
client.make_monthly_payment(account_id="ACC001", amount=500.00)

# Fully repay and close an account early
client.early_repayment(account_id="ACC002")