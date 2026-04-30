import os

from models import Client, CreditAccount

# Ensure database directory exists
if not os.path.exists("dbs"):
    os.makedirs("dbs")


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def wait():
    input("\nPress Enter to continue...")


def print_header(title):
    clear()
    print("\n" + "─" * 50)
    print(f" {title}")
    print("─" * 50)


def get_client():
    print_header("👤 CLIENT ACCESS")
    client_id = input("Enter Client ID: ").strip()
    if not client_id:
        print("❌ Client ID required.")
        wait()
        return None

    # Try to load client
    client = Client(client_id=client_id, name="Unknown", email="unknown@example.com")

    if client.accounts:
        print(f"\n✅ Loaded client: {client.name} (ID: {client.client_id})")
    else:
        print("\n📝 New client will be created on first account addition.")

    # Update basic info
    name = input(f"Name [{client.name}]: ").strip() or client.name
    email = input(f"Email [{client.email}]: ").strip() or client.email
    phone = input(f"Phone [{client.phone}]: ").strip() or client.phone

    client.name = name
    client.email = email
    client.phone = phone

    return client


def view_account_history(client: Client):
    print_header("📋 ACCOUNT HISTORY")
    if not client.accounts:
        print("📭 No accounts found.")
        wait()
        return

    print(f"Client: {client.name}")
    print(f"Total Debt: ${client.total_outstanding_debt():,.2f}\n")

    if client.get_active_accounts():
        print("🟢 ACTIVE ACCOUNTS:")
        for acc in client.get_active_accounts():
            print(f"  • {acc.account_id}")
            print(
                f"     Balance: ${acc.credit_amt:,.2f} \
                    / Limit: ${acc.credit_limit:,.2f}"
            )
            print(f"     Rate: {acc.interest_rate:.1%} | Active")

    if client.get_closed_accounts():
        print("\n🔴 CLOSED ACCOUNTS:")
        for acc in client.get_closed_accounts():
            print(f"  • {acc.account_id} (Closed)")

    wait()


def view_credit_limits(client: Client):
    print_header("📊 CREDIT LIMITS & USAGE")
    if not client.get_active_accounts():
        print("No active accounts.")
        wait()
        return

    print(f"Client: {client.name}\n")
    for acc in client.get_active_accounts():
        utilization = (
            (acc.credit_amt / acc.credit_limit) * 100 if acc.credit_limit > 0 else 0
        )
        print(f"💳 Account: {acc.account_id}")
        print(
            f"   Used: ${acc.credit_amt:,.2f} \
                / ${acc.credit_limit:,.2f} ({utilization:.1f}%)"
        )
        print(f"   Rate: {acc.interest_rate:.1%}")
        print("")

    wait()


def credit_calculator():
    print_header("🧮 CREDIT PAYMENT CALCULATOR")
    try:
        amount = float(input("Loan Amount ($): "))
        rate = float(input("Annual Interest Rate (e.g., 0.12 for 12%): "))
        months = int(input("Duration (months): "))

        result = CreditAccount.calculate_monthly_payment(amount, rate, months)

        print("\n📊 RESULT:")
        print(f"Monthly Payment: ${result['monthly_payment']:,.2f}")
        print(f"Total Repayment: ${result['total_repayment']:,.2f}")
        print(f"Total Interest:  ${result['total_interest']:,.2f}")
    except ValueError as e:
        print(f"\n❌ Error: {e}")
    except Exception:
        print("\n❌ Invalid input.")

    wait()


def suggest_plan(client: Client):
    print_header("💡 CREDIT PLAN SUGGESTION")
    try:
        amount = float(input("Desired Loan Amount ($): "))
        rate = float(input("Expected Annual Rate (e.g., 0.15): "))
        max_pay = float(input("Max Monthly Payment You Can Afford ($): "))

        plan = client.suggest_credit_plan(amount, rate, max_pay)

        if "error" in plan:
            print(f"\n⚠️ {plan['error']}")
        else:
            print("\n✅ Suggested Plan:")
            print(
                f"Duration: {plan['duration_months']} \
                    months ({plan['duration_years']} years)"
            )
            print(f"Monthly Payment: ${plan['monthly_payment']:,.2f}")
            print(f"Total Interest: ${plan['total_interest']:,.2f}")
    except Exception:
        print("\n❌ Invalid input.")

    wait()


def payment_calendar(client: Client):
    print_header("📅 PAYMENT CALENDAR & EARLY REPAIDMENT")
    if not client.get_active_accounts():
        print("No active accounts to simulate.")
        wait()
        return

    # Select account
    print("Active Accounts:")
    accounts = client.get_active_accounts()
    for i, acc in enumerate(accounts, 1):
        print(
            f"{i}. {acc.account_id} - ${acc.credit_amt:,.2f} @ {acc.interest_rate:.1%}"
        )

    try:
        choice = int(input(f"\nSelect account (1-{len(accounts)}): ")) - 1
        account = accounts[choice]
    except (IndexError, ValueError):
        print("❌ Invalid selection.")
        wait()
        return

    try:
        monthly_payment = float(input("Monthly Payment Amount ($): "))
        if monthly_payment <= 0:
            print("❌ Payment must be positive.")
            wait()
            return
    except ValueError:
        print("❌ Invalid number.")
        wait()
        return

    # Simulation
    balance = account.credit_amt
    rate_per_month = account.interest_rate / 12
    month = 0
    total_paid = 0.0

    print(f"\n📅 Simulating repayment of '{account.account_id}'...")
    print(f"{'Mo':<3} {'Balance':<12} {'Payment':<10} {'Interest':<10} {'New Bal'}")
    print("-" * 50)

    while balance > 0 and month < 60:  # Cap at 5 years
        month += 1
        interest = balance * rate_per_month
        applied = min(monthly_payment, balance + interest)  # Cover interest first
        principal_reduction = max(0, applied - interest)
        balance = max(0, balance - principal_reduction)
        total_paid += applied

        print(f"{month:<3} ${balance:<11,.2f}", end=" ")
        print(f"${applied:<9.2f} ${interest:<9.2f} ${balance:.2f}")

        if balance == 0:
            print(f"\n🎉 Paid off in {month} months!")
            break

    print(f"\n💸 Total Paid: ${total_paid:.2f}")
    # saved_with_early = total_paid

    # Early repayment option
    calc_full = CreditAccount.calculate_monthly_payment(
        account.credit_amt, account.interest_rate, 12
    )
    alt_total = calc_full["monthly_payment"] * 12

    print(f"🔁 If paid in 12 equal installments: ${alt_total:.2f}")
    if alt_total > total_paid:
        print(f"✅ You save: ${alt_total - total_paid:.2f} by paying more monthly!")

    wait()


def main_menu():
    client = None
    while True:
        clear()
        print("🏦 Banking App — Main Menu")
        print("────────────────────────────────────")
        if client:
            print(f"Logged in as: {client.name} ({client.client_id})")
        else:
            print("No client selected.")
        print("────────────────────────────────────")
        print("1. Login / Set Client")
        print("2. View Account History")
        print("3. View Credit Limits")
        print("4. Credit Payment Calculator")
        print("5. Get Credit Plan Suggestion")
        print("6. View Payment Calendar & Early Repayment")
        print("7. Exit")
        print("────────────────────────────────────")

        choice = input("Choose an option (1-7): ").strip()

        if choice == "1":
            client = get_client()
        elif choice == "2":
            if client:
                view_account_history(client)
            else:
                print("\n❌ Please select a client first.")
                wait()
        elif choice == "3":
            if client:
                view_credit_limits(client)
            else:
                print("\n❌ Please select a client first.")
                wait()
        elif choice == "4":
            credit_calculator()
        elif choice == "5":
            if client:
                suggest_plan(client)
            else:
                print("\n❌ Please select a client first.")
                wait()
        elif choice == "6":
            if client:
                payment_calendar(client)
            else:
                print("\n❌ Please select a client first.")
                wait()
        elif choice == "7":
            print("\n👋 Thank you for using the Banking App. Goodbye!")
            break
        else:
            print("\n❌ Invalid choice. Please pick 1–7.")
            wait()


if __name__ == "__main__":
    main_menu()
