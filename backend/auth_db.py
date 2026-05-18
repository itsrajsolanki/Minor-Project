
import sqlite3
import hashlib
import os
import secrets

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.db")


def _hash_password(password: str, salt: str) -> str:
    """Return a SHA-256 hex digest of password+salt."""
    return hashlib.sha256((password + salt).encode()).hexdigest()


def init_auth_db() -> None:
    """Create the users table if it does not exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                username  TEXT    NOT NULL UNIQUE,
                email     TEXT    NOT NULL UNIQUE,
                salt      TEXT    NOT NULL,
                password  TEXT    NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()


def register_user(username: str, email: str, password: str) -> dict:
    
    salt = secrets.token_hex(16)
    hashed = _hash_password(password, salt)
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO users (username, email, salt, password) VALUES (?, ?, ?, ?)",
                (username, email, salt, hashed),
            )
            conn.commit()
        return {"success": True}
    except sqlite3.IntegrityError as e:
        if "username" in str(e):
            return {"success": False, "error": "Username already taken."}
        if "email" in str(e):
            return {"success": False, "error": "Email already registered."}
        return {"success": False, "error": str(e)}


def verify_user(username: str, password: str) -> dict:
    
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT salt, password FROM users WHERE username = ?", (username,)
        ).fetchone()

    if not row:
        return {"success": False, "error": "Invalid username or password."}

    salt, stored_hash = row
    if _hash_password(password, salt) == stored_hash:
        return {"success": True, "username": username}
    return {"success": False, "error": "Invalid username or password."}


# Auto-initialise on import
init_auth_db()
