# models.py
import sqlite3
from datetime import datetime
from typing import List, Optional


class CreditAccount:
    def __init__(
        self,
        client_id: str,
        account_id: str,
        interest_rate: float = 0.0,
        credit_limit: float = 0.0,
        credit_amt: float = 0.0,
        principal: float = None,
        is_active: bool = True,
        db_path: str = "dbs/accounts.db"
    ):
        self.client_id = client_id
        self.account_id = account_id
        self.interest_rate = interest_rate
        self.credit_limit = credit_limit
        self.credit_amt = credit_amt
        self.principal = principal
        self.is_active = is_active
        self.db_path = db_path
        

    def _initialize_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_accounts (
                client_id TEXT NOT NULL,
                account_id TEXT PRIMARY KEY,
                interest_rate REAL NOT NULL,
                credit_limit REAL NOT NULL,
                credit_amt REAL NOT NULL,
                principal REAL,               -- Track original borrowed amount
                is_active INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def save(self):
        self._initialize_db()  # Ensure table exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        now = datetime.now().isoformat()

        cursor.execute('''
            INSERT OR REPLACE INTO credit_accounts
            (client_id, account_id, interest_rate, credit_limit, credit_amt, principal, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.client_id,
            self.account_id,
            self.interest_rate,
            self.credit_limit,
            self.credit_amt,
            self.principal, 
            int(self.is_active),
            now if not self._exists() else self._get_created_at(),
            now
        ))

        conn.commit()
        conn.close()

    def _exists(self) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM credit_accounts WHERE account_id = ?", (self.account_id,))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def _get_created_at(self) -> str:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT created_at FROM credit_accounts WHERE account_id = ?", (self.account_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else datetime.now().isoformat()

    def close_account(self):
        self.is_active = False
        self.save()

    def apply_monthly_interest(self, max_interest_ratio: float = 0.5) -> dict:
        """
        Apply monthly interest only if total interest doesn't exceed a cap.
        Default: Interest cannot exceed max_interest_ratio (e.g., 50%) of credit limit.

        Args:
            max_interest_ratio (float): Max ratio of interest relative to credit limit (default 0.5)

        Returns:
            dict: Result message or error
        """
        if not self.is_active:
            return {"error": "Account is closed."}

        # Calculate current interest paid so far
        total_interest_paid = self.credit_amt - self._get_principal_start()

        # How much interest we're about to add
        monthly_rate = self.interest_rate / 12
        interest_for_this_month = self.credit_amt * monthly_rate

        # Maximum allowed total interest
        max_allowed_interest = self.credit_limit * max_interest_ratio

        # Will this push us over the cap?
        if total_interest_paid + interest_for_this_month > max_allowed_interest:
            remaining_interest = max_allowed_interest - total_interest_paid
            if remaining_interest <= 0:
                return {
                    "warning": f"Interest cap reached ({max_interest_ratio:.0%} of limit). "
                               f"No more interest will be charged."
                }

            # Prorate: only apply partial interest
            effective_rate = remaining_interest / self.credit_amt
            self.credit_amt *= (1 + effective_rate)
            self.save()
            return {
                "message": f"Partial interest applied (capped). "
                           f"New balance: ${self.credit_amt:.2f}. Interest cap reached.",
                "capped": True
            }

        # Normal case: apply full interest
        self.credit_amt *= (1 + monthly_rate)
        self.save()
        return {"message": f"Interest applied. New balance: ${self.credit_amt:.2f}"}

    def _get_principal_start(self) -> float:
        """Return the original principal amount."""
        return self.principal or self.credit_limit

        def update_balance(self, amount: float):
            if amount > self.credit_limit:
                raise ValueError(f"Amount {amount} exceeds limit {self.credit_limit}")
            self.credit_amt = amount
            self.save()

    @staticmethod
    def get_accounts_by_client(client_id: str, db_path: str = "dbs/accounts.db") -> List['CreditAccount']:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT account_id, interest_rate, credit_limit, credit_amt, is_active
            FROM credit_accounts WHERE client_id = ?
        ''', (client_id,))
        rows = cursor.fetchall()
        conn.close()

        accounts = []
        for row in rows:
            acct = CreditAccount(
                client_id=client_id,
                account_id=row[0],
                interest_rate=row[1],
                credit_limit=row[2],
                credit_amt=row[3],
                is_active=bool(row[4]),
                db_path=db_path
            )
            accounts.append(acct)
        return accounts

    def to_dict(self):
        return {
            "account_id": self.account_id,
            "client_id": self.client_id,
            "interest_rate": self.interest_rate,
            "credit_limit": self.credit_limit,
            "credit_amt": self.credit_amt,
            "is_active": self.is_active
        }
        
    @staticmethod
    def calculate_monthly_payment(
        credit_amount: float,
        annual_interest_rate: float,
        duration_months: int
    ) -> dict:
        """
        Calculate monthly payment and total repayment using the loan amortization formula.
        
        Args:
            credit_amount: The loan/principal amount
            annual_interest_rate: Annual interest rate (e.g., 0.15 for 15%)
            duration_months: Number of months
        
        Returns:
            Dict with monthly_payment, total_repayment, total_interest
        """
        if credit_amount <= 0:
            raise ValueError("Credit amount must be positive.")
        if annual_interest_rate < 0:
            raise ValueError("Interest rate cannot be negative.")
        if duration_months <= 0:
            raise ValueError("Duration must be a positive number of months.")

        monthly_rate = annual_interest_rate / 12  # Monthly interest rate

        if monthly_rate == 0:
            monthly_payment = credit_amount / duration_months
        else:
            # Amortization formula
            monthly_payment = credit_amount * (monthly_rate * (1 + monthly_rate)**duration_months) / \
                            (((1 + monthly_rate)**duration_months) - 1)

        total_repayment = monthly_payment * duration_months
        total_interest = total_repayment - credit_amount

        return {
            "monthly_payment": round(monthly_payment, 2),
            "total_repayment": round(total_repayment, 2),
            "total_interest": round(total_interest, 2)
        }
        
    def update_credit_limit(self, new_limit: float, force: bool = False):
        """
        Update the credit limit for this account.

        Args:
            new_limit (float): New credit limit
            force (bool): If True, allows limit < current balance

        Returns:
            dict: Result message or error
        """
        if new_limit <= 0:
            return {"error": "Credit limit must be positive."}

        if not self.is_active:
            return {"error": "Cannot modify limit on a closed account."}

        if new_limit < self.credit_amt and not force:
            return {
                "error": f"New limit (${new_limit:.2f}) is below current balance (${self.credit_amt:.2f}). "
                        "Use force=True to override."
            }

        self.credit_limit = new_limit
        self.save()
        return {
            "message": f"Credit limit updated to ${self.credit_limit:,.2f}.",
            "warning": "Balance exceeds limit." if new_limit < self.credit_amt else None
        }

    def __repr__(self):
        status = "Active" if self.is_active else "Closed"
        return (f"CreditAccount(id='{self.account_id}', rate={self.interest_rate:.1%}, "
                f"limit=${self.credit_limit:,.2f}, balance=${self.credit_amt:,.2f}, status={status})")
        
    # --- Dynamic Interest Rate Engine ---
class DynamicRateEngine:
    """
    A rule-based engine that returns an annual interest rate based on loan duration.
    Can use tiered or interpolated rates.
    """

    # Define rate tiers: (min_duration_months, rate_as_decimal)
    DEFAULT_TIERS = [
        (6,   0.18),   # 18% for 6–12 months
        (13,  0.16),   # 16% for 13–24 months
        (25,  0.15),   # 15% for 25–36 months
        (37,  0.14),   # 14% for 37–60 months
        (61,  0.135),  # 13.5% for 61–84 months
        (85,  0.13),   # 13% for 85+ months
    ]

    def __init__(self, rate_tiers=None):
        """
        Args:
            rate_tiers: List of tuples [(min_months, rate), ...], sorted by duration
        """
        self.tiers = rate_tiers or self.DEFAULT_TIERS

    def get_rate(self, duration_months: int) -> float:
        """
        Get the applicable annual interest rate based on duration.

        Args:
            duration_months (int): Loan term in months

        Returns:
            float: Annual interest rate (e.g., 0.15 for 15%)
        """
        if duration_months < self.tiers[0][0]:
            # If shorter than minimum, return highest rate
            return self.tiers[0][1]

        # Find the longest tier <= duration
        rate = self.tiers[0][1]  # default fallback
        for min_months, tier_rate in self.tiers:
            if duration_months >= min_months:
                rate = tier_rate
            else:
                break
        return rate

    def get_suggested_rate(self, amount: float, max_payment: float) -> dict:
        """
        Suggest the best feasible duration and its corresponding rate/payment.

        Args:
            amount: Loan amount
            max_payment: Max affordable monthly payment

        Returns:
            dict: Contains duration, rate, payment, total interest
        """
        for months in range(6, 121):
            rate = self.get_rate(months)
            calc = CreditAccount.calculate_monthly_payment(amount, rate, months)
            if calc["monthly_payment"] <= max_payment:
                return {
                    "duration_months": months,
                    "duration_years": round(months / 12, 1),
                    "annual_interest_rate": rate,
                    "monthly_payment": calc["monthly_payment"],
                    "total_interest": calc["total_interest"]
                }
        return {"error": "No plan fits your budget within 10 years."}


class Client:
    def __init__(
        self,
        client_id: str,
        name: str,
        email: str,
        phone: str = "",
        db_path: str = "dbs/accounts.db"
    ):
        self.client_id = client_id
        self.name = name
        self.email = email
        self.phone = phone
        self.db_path = db_path
        self.accounts = CreditAccount.get_accounts_by_client(self.client_id, self.db_path)

    def add_credit_account(
        self,
        account_id: str,
        interest_rate: float,
        credit_limit: float,
        initial_amount: float = 0.0
    ) -> CreditAccount:
        if any(acc.account_id == account_id for acc in self.accounts):
            raise ValueError(f"Account ID '{account_id}' already exists.")

        new_account = CreditAccount(
            client_id=self.client_id,
            account_id=account_id,
            interest_rate=interest_rate,
            credit_limit=credit_limit,
            credit_amt=initial_amount,
            db_path=self.db_path
        )
        new_account.save()
        self.accounts.append(new_account)
        return new_account

    def get_active_accounts(self) -> List[CreditAccount]:
        return [acc for acc in self.accounts if acc.is_active]

    def get_closed_accounts(self) -> List[CreditAccount]:
        return [acc for acc in self.accounts if not acc.is_active]

    def total_outstanding_debt(self) -> float:
        return sum(acc.credit_amt for acc in self.get_active_accounts())

    def make_monthly_payment(self, account_id: str, amount: float) -> dict:
        if amount <= 0:
            return {"error": "Payment must be greater than zero."}

        account = self._get_account(account_id)
        if not account:
            return {"error": f"Account '{account_id}' not found."}

        if not account.is_active:
            return {"error": "Cannot pay on a closed account."}

        new_balance = max(0.0, account.credit_amt - amount)
        try:
            account.update_balance(new_balance)
            return {
                "message": f"Payment of ${amount:.2f} applied.",
                "new_balance": round(new_balance, 2)
            }
        except ValueError as e:
            return {"error": str(e)}

    def early_repayment(self, account_id: str) -> dict:
        account = self._get_account(account_id)
        if not account:
            return {"error": "Account not found."}
        if not account.is_active:
            return {"error": "Account already closed."}

        account.update_balance(0.0)
        account.close_account()
        return {"message": f"Account '{account_id}' fully repaid and closed."}

    def _get_account(self, account_id: str) -> Optional[CreditAccount]:
        return next((acc for acc in self.accounts if acc.account_id == account_id), None)

    def to_dict(self):
        return {
            "client_id": self.client_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "total_debt": round(self.total_outstanding_debt(), 2),
            "active_accounts": len(self.get_active_accounts()),
            "closed_accounts": len(self.get_closed_accounts())
        }
        
    def suggest_credit_plan(
        self,
        credit_amount: float,
        max_payment: float,
        rate_engine: DynamicRateEngine = None
    ) -> dict:
        """
        Suggest a credit plan where interest rate depends on loan duration.

        Args:
            credit_amount (float): Desired loan amount
            max_payment (float): Maximum monthly payment client can afford
            rate_engine (DynamicRateEngine): Custom rate rules (optional)

        Returns:
            dict: Best feasible plan with rate, term, cost
        """
        engine = rate_engine or DynamicRateEngine()

        return engine.get_suggested_rate(credit_amount, max_payment)