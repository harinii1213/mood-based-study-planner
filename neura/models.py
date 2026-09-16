import sqlite3
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash


def get_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: str) -> None:
    conn = get_db(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


class User:
    """A registered Neura user, backed by the `users` SQLite table."""

    def __init__(self, row: sqlite3.Row):
        self.id = row["id"]
        self.name = row["name"]
        self.email = row["email"]
        self.password_hash = row["password_hash"]
        self.created_at = datetime.fromisoformat(row["created_at"])

    @staticmethod
    def get_by_id(db_path: str, user_id: int):
        conn = get_db(db_path)
        try:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        finally:
            conn.close()
        return User(row) if row else None

    @staticmethod
    def get_by_email(db_path: str, email: str):
        conn = get_db(db_path)
        try:
            row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        finally:
            conn.close()
        return User(row) if row else None

    @staticmethod
    def create(db_path: str, name: str, email: str, password: str) -> "User":
        password_hash = generate_password_hash(password)
        created_at = datetime.now(timezone.utc).isoformat()
        conn = get_db(db_path)
        try:
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (name, email, password_hash, created_at),
            )
            conn.commit()
            user_id = cursor.lastrowid
        finally:
            conn.close()
        return User.get_by_id(db_path, user_id)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)
