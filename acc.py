import sqlite3
from datetime import datetime

class BankAccount:
    def __init__(self, client_id, interest_rate=0.0, credit_limit=0.0, credit_amt=0.0, db_path="dbs/accounts.db"):
        """
        Initialize a BankAccount for a client with interest rate, limits, and balance.
        
        Args:
            client_id (str): Unique identifier for the client
            interest_rate (float): Annual interest rate (e.g., 0.05 for 5%)
            credit_limit (float): Maximum credit allowed
            credit_amt (float): Current outstanding balance
            db_path (str): Path to the SQLite database file
        """
        self.client_id = client_id
        self.interest_rate = interest_rate
        self.credit_limit = credit_limit
        self.credit_amt = credit_amt
        self.db_path = db_path

        # Ensure the database and table exist
        self._initialize_db()

    def _initialize_db(self):
        """Create the database and accounts table if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                client_id TEXT PRIMARY KEY,
                interest_rate REAL NOT NULL,
                credit_limit REAL NOT NULL,
                credit_amt REAL NOT NULL,
                updated_at TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def save(self):
        """Save or update the account in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()

        cursor.execute('''
            INSERT OR REPLACE INTO accounts (client_id, interest_rate, credit_limit, credit_amt, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.client_id, self.interest_rate, self.credit_limit, self.credit_amt, timestamp))

        conn.commit()
        conn.close()
        print(f"Account for client '{self.client_id}' saved successfully.")

    def load(self):
        """Load account data from the database by client_id."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT interest_rate, credit_limit, credit_amt, updated_at FROM accounts WHERE client_id = ?', 
                       (self.client_id,))
        row = cursor.fetchone()
        conn.close()

        if row:
            self.interest_rate, self.credit_limit, self.credit_amt, updated_at = row
            print(f"Account loaded for client '{self.client_id}', last updated: {updated_at}")
            return True
        else:
            print(f"No account found for client '{self.client_id}'")
            return False

    def update_credit_amt(self, amount):
        """Update the current credit amount (e.g., after a purchase or payment)."""
        if amount > self.credit_limit:
            raise ValueError("Credit amount exceeds credit limit.")
        self.credit_amt = amount
        self.save()

    def apply_monthly_interest(self):
        """Apply monthly interest to the current credit amount."""
        monthly_rate = self.interest_rate / 12
        self.credit_amt *= (1 + monthly_rate)
        self.save()
        print(f"Applied monthly interest. New balance: ${self.credit_amt:.2f}")

    def __repr__(self):
        return (f"BankAccount(client_id='{self.client_id}', interest_rate={self.interest_rate}, "
                f"credit_limit={self.credit_limit}, credit_amt={self.credit_amt})")