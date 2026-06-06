import re
import sqlite3
import hashlib
import os
from pathlib import Path
from typing import Tuple


class RegistrationError(Exception):
    pass


class UserRegistration:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def _validate_username(self, username: str) -> None:
        if not username or len(username) < 3 or len(username) > 50:
            raise RegistrationError("Username must be 3-50 characters long")
        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            raise RegistrationError("Username can only contain letters, numbers, hyphens, and underscores")

    def _validate_email(self, email: str) -> None:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email):
            raise RegistrationError("Invalid email format")

    def _validate_password(self, password: str) -> None:
        if not password or len(password) < 8:
            raise RegistrationError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in password):
            raise RegistrationError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in password):
            raise RegistrationError("Password must contain at least one digit")

    def _hash_password(self, password: str) -> str:
        salt = os.urandom(32)
        pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return (salt + pwd_hash).hex()

    def _check_username_exists(self, username: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            return cursor.fetchone() is not None

    def _check_email_exists(self, email: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT 1 FROM users WHERE email = ?", (email,))
            return cursor.fetchone() is not None

    def register(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        try:
            username = username.strip()
            email = email.strip().lower()
            
            self._validate_username(username)
            self._validate_email(email)
            self._validate_password(password)
            
            if self._check_username_exists(username):
                raise RegistrationError("Username already exists")
            if self._check_email_exists(email):
                raise RegistrationError("Email already registered")
            
            password_hash = self._hash_password(password)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                    (username, email, password_hash)
                )
                conn.commit()
            
            return True, "Registration successful"
        
        except RegistrationError as e:
            return False, str(e)
        except sqlite3.IntegrityError:
            return False, "Registration failed due to database constraint"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"


if __name__ == "__main__":
    reg = UserRegistration()
    
    test_cases = [
        ("john_doe", "john@example.com", "SecurePass123"),
        ("jane_smith", "jane@example.com", "MyPassword456"),
        ("ab", "invalid@email", "weak"),
    ]
    
    for username, email, password in test_cases:
        success, message = reg.register(username, email, password)
        print(f"{'✓' if success else '✗'} {username}: {message}")