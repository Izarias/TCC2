import os
import re
import sqlite3
from datetime import datetime

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash

DB_PATH = os.environ.get("APP_DB_PATH", "app.db")
PASSWORD_MIN_LEN = 8

app = Flask(__name__)


def db_connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with db_connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            INSERT OR IGNORE INTO users (username, password_hash, updated_at)
            VALUES (?, ?, ?)
            """,
            ("demo", generate_password_hash("Demo1234!"), datetime.utcnow().isoformat(timespec="seconds") + "Z"),
        )


def is_strong_enough(password: str) -> bool:
    if len(password) < PASSWORD_MIN_LEN:
        return False
    has_letter = re.search(r"[A-Za-z]", password) is not None
    has_digit = re.search(r"\d", password) is not None
    return has_letter and has_digit


@app.post("/password/update")
def update_password():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    old_password = payload.get("old_password") or ""
    new_password = payload.get("new_password") or ""

    if not username or not old_password or not new_password:
        return jsonify({"ok": False, "error": "missing_fields"}), 400

    if old_password == new_password:
        return jsonify({"ok": False, "error": "password_unchanged"}), 400

    if not is_strong_enough(new_password):
        return jsonify({"ok": False, "error": "weak_password", "min_len": PASSWORD_MIN_LEN}), 400

    with db_connect() as conn:
        user = conn.execute(
            "SELECT id, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()

        if user is None:
            return jsonify({"ok": False, "error": "user_not_found"}), 404

        if not check_password_hash(user["password_hash"], old_password):
            return jsonify({"ok": False, "error": "invalid_credentials"}), 401

        conn.execute(
            "UPDATE users SET password_hash = ?, updated_at = ? WHERE id = ?",
            (
                generate_password_hash(new_password),
                datetime.utcnow().isoformat(timespec="seconds") + "Z",
                user["id"],
            ),
        )

    return jsonify({"ok": True, "username": username}), 200


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)