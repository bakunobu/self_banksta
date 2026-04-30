# database.py
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "users.db")


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                bank_spread REAL DEFAULT 0.03
            )
        """
        )
        conn.commit()


def get_user_spread(user_id: int) -> float:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT bank_spread FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        return row[0] if row else 0.03


def set_user_spread(user_id: int, username: str, spread: float):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO users (user_id, username, bank_spread)
            VALUES (?, ?,
            COALESCE((SELECT bank_spread FROM users WHERE user_id=?), 0.03)
            )
        """,
            (user_id, username, user_id),
        )
        cur.execute(
            "UPDATE users SET bank_spread = ? WHERE user_id = ?", (spread, user_id)
        )
        conn.commit()
