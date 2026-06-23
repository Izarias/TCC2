import base64
import binascii
import hashlib
import hmac
import os
import re
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Tuple

from flask import Flask, jsonify, request

DB_PATH = os.environ.get("APP_DB_PATH", "app.db")
PBKDF2_ITERATIONS = int(os.environ.get("APP_PBKDF2_ITERS", "210000"))

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


app = Flask(__name__)


@dataclass(frozen=True)
class ValidationError(Exception):
    message: str
    field: str = "detail"


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )


def json_error(status: int, message: str, field: str = "detail"):
    return jsonify({"error": message, "field": field}), status


def require_json() -> Dict[str, Any]:
    if not request.is_json:
        raise ValidationError("Expected JSON request body.", "content_type")
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Invalid JSON body.", "body")
    return data


def normalize_username(username: str) -> str:
    return username.strip()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def validate_username(username: str) -> str:
    if not isinstance(username, str):
        raise ValidationError("Username must be a string.", "username")
    username = normalize_username(username)
    if not USERNAME_RE.fullmatch(username):
        raise ValidationError("Username must be 3-32 chars (letters, numbers, underscore).", "username")
    return username


def validate_email(email: str) -> str:
    if not isinstance(email, str):
        raise ValidationError("Email must be a string.", "email")
    email = normalize_email(email)
    if len(email) > 254 or not EMAIL_RE.fullmatch(email):
        raise ValidationError("Invalid email address.", "email")
    return email


def validate_password(password: str) -> str:
    if not isinstance(password, str):
        raise ValidationError("Password must be a string.", "password")
    if len(password) < 10 or len(password) > 200:
        raise ValidationError("Password must be 10-200 characters.", "password")
    if password.strip() != password:
        raise ValidationError("Password must not start or end with whitespace.", "password")
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(not c.isalnum() for c in password)
    if sum([has_lower, has_upper, has_digit, has_symbol]) < 3:
        raise ValidationError("Password must include 3 of: lowercase, uppercase, digit, symbol.", "password")
    return password


def hash_password(password: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
    salt_b64 = base64.b64encode(salt).decode("ascii")
    dk_b64 = base64.b64encode(dk).decode("ascii")
    return f"pbkdf2_sha256${iterations}${salt_b64}${dk_b64}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters_s, salt_b64, dk_b64 = stored.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters_s)
        salt = base64.b64decode(salt_b64.encode("ascii"))
        expected = base64.b64decode(dk_b64.encode("ascii"))
    except (ValueError, binascii.Error):
        return False

    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=len(expected))
    return hmac.compare_digest(actual, expected)


def parse_registration_payload(data: Dict[str, Any]) -> Tuple[str, str, str]:
    username = validate_username(data.get("username"))
    email = validate_email(data.get("email"))
    password = validate_password(data.get("password"))
    return username, email, password


def is_unique_violation(exc: sqlite3.IntegrityError) -> bool:
    msg = str(exc).lower()
    return "unique constraint failed" in msg or "unique constraint" in msg


@app.post("/register")
def register():
    try:
        data = require_json()
        username, email, password = parse_registration_payload(data)
        password_hash = hash_password(password)

        with get_db() as conn:
            conn.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash),
            )
            user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        return jsonify({"id": user_id, "username": username, "email": email}), 201

    except ValidationError as e:
        return json_error(400, e.message, e.field)

    except sqlite3.IntegrityError as e:
        if is_unique_violation(e):
            return json_error(409, "Username or email already exists.", "conflict")
        return json_error(500, "Database error.", "database")

    except Exception:
        return json_error(500, "Unexpected server error.", "server")


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=False)