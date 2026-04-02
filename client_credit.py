import sqlite3
from datetime import datetime
from typing import List, Optional


class CreditAccount:
    """
    Represents a credit account (current or past) for a client.
    Can be a loan, credit line, etc.
    """
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

        self._initialize_db()

    def _initialize_db(self):
        """Create the database and table if not exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credit_accounts (
                client_id TEXT NOT NULL,
                account_id TEXT PRIMARY KEY,
                interest_rate REAL NOT NULL,
                credit_limit REAL NOT NULL,
                credit_amt REAL NOT NULL,
                is_active INTEGER NOT NULL,  -- 1 for True, 0 for False
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def save(self):
        """Insert or update the credit account."""
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
        status = "updated" if self._exists() else "created"
        print(f"Credit account '{self.account_id}' {status} for client '{self.client_id}'.")

    def _exists(self) -> bool:
        """Check if this account already exists in DB."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM credit_accounts WHERE account_id = ?", (self.account_id,))
        row = cursor.fetchone()
        conn.close()
        return row is not None

    def _get_created_at(self) -> str:
        """Get creation timestamp from DB if exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT created_at FROM credit_accounts WHERE account_id = ?", (self.account_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else datetime.now().isoformat()

    def close_account(self):
        """Mark the account as inactive (past credit)."""
        self.is_active = False
        self.save()
        print(f"Account '{self.account_id}' has been closed.")

    def apply_monthly_interest(self):
        """Apply monthly interest if account is active."""
        if not self.is_active:
            print(f"Cannot apply interest: Account '{self.account_id}' is closed.")
            return
        monthly_rate = self.interest_rate / 12
        self.credit_amt *= (1 + monthly_rate)
        self.save()
        print(f"Applied monthly interest. New balance: ${self.credit_amt:.2f}")

    def update_balance(self, amount: float):
        """Update credit amount, ensuring it doesn't exceed limit."""
        if amount > self.credit_limit:
            raise ValueError(f"Amount {amount} exceeds credit limit {self.credit_limit}")
        self.credit_amt = amount
        self.save()

    @staticmethod
    def get_accounts_by_client(client_id: str, db_path: str = "dbs/accounts.db") -> List['CreditAccount']:
        """Load all credit accounts (active and inactive) for a given client."""
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

    def __repr__(self):
        status = "Active" if self.is_active else "Closed"
        return (f"CreditAccount(id='{self.account_id}', client='{self.client_id}', "
                f"rate={self.interest_rate:.1%}, limit=${self.credit_limit:,.2f}, "
                f"balance=${self.credit_amt:,.2f}, status={status})")


class Client:
    """
    Represents a banking client with personal info and their credit accounts.
    """
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

        # Load associated credit accounts
        self.accounts: List[CreditAccount] = CreditAccount.get_accounts_by_client(self.client_id, self.db_path)

    def add_credit_account(
        self,
        account_id: str,
        interest_rate: float,
        credit_limit: float,
        initial_amount: float = 0.0
    ) -> CreditAccount:
        """Create and link a new credit account."""
        if any(acc.account_id == account_id for acc in self.accounts):
            raise ValueError(f"Account ID '{account_id}' already exists for this client.")

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
        print(f"New credit account '{account_id}' added for {self.name}.")
        return new_account

    def get_active_accounts(self) -> List[CreditAccount]:
        """Return only active credit accounts."""
        return [acc for acc in self.accounts if acc.is_active]

    def get_closed_accounts(self) -> List[CreditAccount]:
        """Return closed (past) credit accounts."""
        return [acc for acc in self.accounts if not acc.is_active]

    def total_outstanding_debt(self) -> float:
        """Sum of all current balances on active accounts."""
        return sum(acc.credit_amt for acc in self.get_active_accounts())

    def __repr__(self):
        return (f"Client(id='{self.client_id}', name='{self.name}', email='{self.email}', "
                f"phone='{self.phone}', active_accounts={len(self.get_active_accounts())})")