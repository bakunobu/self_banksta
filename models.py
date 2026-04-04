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
        is_active: bool = True,
        db_path: str = "dbs/accounts.db"
    ):
        self.client_id = client_id
        self.account_id = account_id
        self.interest_rate = interest_rate
        self.credit_limit = credit_limit
        self.credit_amt = credit_amt
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
            (client_id, account_id, interest_rate, credit_limit, credit_amt, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            self.client_id,
            self.account_id,
            self.interest_rate,
            self.credit_limit,
            self.credit_amt,
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

    def apply_monthly_interest(self):
        if not self.is_active:
            return {"error": "Account is closed."}
        monthly_rate = self.interest_rate / 12
        self.credit_amt *= (1 + monthly_rate)
        self.save()
        return {"message": f"Interest applied. New balance: ${self.credit_amt:.2f}"}

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

    def __repr__(self):
        status = "Active" if self.is_active else "Closed"
        return (f"CreditAccount(id='{self.account_id}', rate={self.interest_rate:.1%}, "
                f"limit=${self.credit_limit:,.2f}, balance=${self.credit_amt:,.2f}, status={status})")


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