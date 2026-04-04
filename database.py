# database.py
import os
import sqlite3
from models import CreditAccount

def init_db():
    """Initialize the database and create tables."""
    os.makedirs("dbs", exist_ok=True)
    # Creating an instance will trigger table creation
    dummy = CreditAccount(client_id="init", account_id="init")
    print("Database initialized.")