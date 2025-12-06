# db.py
import sqlite3
from typing import Optional, Dict, Any

DB_PATH = "app.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # return rows as dict-like
    return conn


def init_db() -> None:
    """
    Create the users table and insert some demo data if empty.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                active INTEGER NOT NULL
            )
            """
        )
        conn.commit()

        # Check if table is empty
        cur.execute("SELECT COUNT(*) AS cnt FROM users")
        count = cur.fetchone()["cnt"]

        if count == 0:
            print("[DB] Seeding demo data...")
            demo_users = [
                (1, "Alice", "alice@example.com", 1),
                (2, "Bob", "bob@example.com", 1),
                (3, "Charlie", "charlie@example.com", 0),
            ]
            cur.executemany(
                "INSERT INTO users (id, name, email, active) VALUES (?, ?, ?, ?)",
                demo_users,
            )
            conn.commit()
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Load a user from the database by ID.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, name, email, active FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if row is None:
            return None

        # Convert SQLite Row to normal dict
        return {
            "id": row["id"],
            "name": row["name"],
            "email": row["email"],
            "active": bool(row["active"]),
        }
    finally:
        conn.close()

