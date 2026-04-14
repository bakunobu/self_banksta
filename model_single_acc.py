import sqlite3
from datetime import datetime
from typing import List, Optional
from cb_parser import ParseKeyRates

class CreditAccount:
    def __init__(
        self,
        client_id: str,
        db_path:str = "dbs/single_acc.db"
    ):
        self.client_id = client_id
        self.db_path = db_path
        self._initialize_dbs()
    
    def _initialize_dbs(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credit_account (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                       """)
        
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY,
                account_id INTEGER,
                principal REAL,
                interest_rate REAL,
                duration REAL,
                is_active BOOLEAN,
                number_of_payments INTEGER,
                created_at TEXT,
                updated_at TEXT,
                FOREIGN KEY (account_id) REFERENCES credit_account(account_id)
                )"""
            )
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY,
                account_id INTEGET,
                product_id INTEGER,
                payment_amount REAL,
                payment_date TEXT,
                FOREIGN KEY (account_id) REFERENCES credit_account(account_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
                """
                )
        
        conn.commit()
        conn.close()
    
    def create_credit_account(self, account_id: str, interest_rate: float, credit_limit: float, credit_amt: float, is_active: bool = True):
