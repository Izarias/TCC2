import base64
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import time
from dataclasses import dataclass
from typing import Any, Optional

from flask import Flask, Response, g, jsonify, redirect, request

APP_SECRET = os.environ.get("APP_SECRET", secrets.token_hex(32))
DB_PATH = os.environ.get("DB_PATH", "app.db")

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,32}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PBKDF2_ITERATIONS = int(os.environ.get("PBKDF2_ITERATIONS", "200000"))
PBKDF2_SALT_BYTES = 16
PBKDF2_HASH_BYTES = 32


app = Flask(__name__)
app.config.update(SECRET_KEY=APP_SECRET)


def get_db() -> sqlite3.Connection:
    db = getattr(g, "_db", None)
    if db is None:
        db = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON;")
        db.execute("PRAGMA journal_mode = WAL;")
        g._db = db
    return db


@app.teardown_appcontext
def close_db(_: Optional[BaseException]) -> None:
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    try:
        db.execute("PRAGMA foreign_keys = ON;")
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at INTEGER NOT NULL
            );
            """
        )
        db.commit()
    finally:
        db.close()


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("ascii"))


def hash_password(password: str) -> str:
    if not isinstance(password, str):
        raise ValueError("password must be a string")

    salt = secrets.token_bytes(PBKDF2_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=PBKDF2_HASH_BYTES,
    )
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64e(salt)}${_b64e(dk)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algo, iters_s, salt_b64, dk_b64 = encoded.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iters = int(iters_s)
        salt = _b64d(salt_b64)
        expected = _b64d(dk_b64)
    except Exception:
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iters,
        dklen=len(expected),
    )
    return hmac.compare_digest(actual, expected)


@dataclass(frozen=True)
class ValidationError:
    field: str
    message: str


def validate_registration(username: Any, email: Any, password: Any) -> list[ValidationError]:
    errors: list[ValidationError] = []

    if not isinstance(username, str) or not username.strip():
        errors.append(ValidationError("username", "Username is required."))
    else:
        u = username.strip()
        if not USERNAME_RE.fullmatch(u):
            errors.append(
                ValidationError(
                    "username",
                    "Username must be 3-32 chars and contain only letters, numbers, or underscore.",
                )
            )

    if not isinstance(email, str) or not email.strip():
        errors.append(ValidationError("email", "Email is required."))
    else:
        e = email.strip().lower()
        if len(e) > 254 or not EMAIL_RE.fullmatch(e):
            errors.append(ValidationError("email", "Email is not valid."))

    if not isinstance(password, str) or not password:
        errors.append(ValidationError("password", "Password is required."))
    else:
        if len(password) < 8:
            errors.append(ValidationError("password", "Password must be at least 8 characters."))
        if len(password) > 128:
            errors.append(ValidationError("password", "Password must be at most 128 characters."))

    return errors


def is_json_request() -> bool:
    return request.is_json or "application/json" in (request.headers.get("Accept") or "")


def json_error(message: str, status: int, errors: Optional[list[ValidationError]] = None) -> Response:
    payload: dict[str, Any] = {"ok": False, "message": message}
    if errors:
        payload["errors"] = [{"field": e.field, "message": e.message} for e in errors]
    return jsonify(payload), status


def create_user(username: str, email: str, password: str) -> tuple[bool, Optional[str]]:
    db = get_db()
    now = int(time.time())
    pw_hash = hash_password(password)

    try:
        db.execute(
            "INSERT INTO users (username, email, password_hash, created_at) VALUES (?, ?, ?, ?);",
            (username.strip(), email.strip().lower(), pw_hash, now),
        )
        db.commit()
        return True, None
    except sqlite3.IntegrityError as ex:
        msg = str(ex).lower()
        if "users.username" in msg or "username" in msg:
            return False, "Username is already taken."
        if "users.email" in msg or "email" in msg:
            return False, "Email is already registered."
        return False, "Could not create user."
    except Exception:
        return False, "Could not create user."


REGISTER_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Register</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; }
    form { max-width: 420px; display: grid; gap: 0.75rem; }
    label { display: grid; gap: 0.25rem; font-weight: 600; }
    input { padding: 0.6rem 0.7rem; font-size: 1rem; }
    button { padding: 0.7rem; font-size: 1rem; cursor: pointer; }
    .hint { color: #444; font-size: 0.9rem; }
    .error { color: #b00020; }
  </style>
</head>
<body>
  <h1>Create account</h1>
  <p class="hint">Username: 3-32 chars (letters/numbers/_). Password: 8+ chars.</p>

  {% if error %}
    <p class="error">{{ error }}</p>
  {% endif %}

  <form method="post" action="/register" autocomplete="on">
    <label>
      Username
      <input name="username" type="text" required minlength="3" maxlength="32" />
    </label>
    <label>
      Email
      <input name="email" type="email" required maxlength="254" />
    </label>
    <label>
      Password
      <input name="password" type="password" required minlength="8" maxlength="128" />
    </label>
    <button type="submit">Register</button>
  </form>
</body>
</html>
"""


SUCCESS_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Registered</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin: 2rem; }
    a { color: inherit; }
  </style>
</head>
<body>
  <h1>Registration successful</h1>
  <p>You can now log in (not implemented in this example).</p>
  <p><a href="/register">Back</a></p>
</body>
</html>
"""


@app.get("/")
def home() -> Response:
    return redirect("/register", code=302)


@app.get("/register")
def register_form() -> Response:
    # Inline minimal templating without extra dependencies
    html = REGISTER_HTML.replace("{% if error %}", "").replace("{% endif %}", "").replace("{{ error }}", "")
    return Response(html, mimetype="text/html")


@app.post("/register")
def register_submit() -> Response:
    username = request.form.get("username", "")
    email = request.form.get("email", "")
    password = request.form.get("password", "")

    errors = validate_registration(username, email, password)
    if errors:
        if is_json_request():
            return json_error("Validation failed.", 400, errors)
        first = errors[0].message
        html = REGISTER_HTML.replace("{% if error %}", "").replace("{% endif %}", "").replace("{{ error }}", first)
        return Response(html, status=400, mimetype="text/html")

    ok, err = create_user(username, email, password)
    if not ok:
        if is_json_request():
            return json_error(err or "Registration failed.", 409)
        html = REGISTER_HTML.replace("{% if error %}", "").replace("{% endif %}", "").replace("{{ error }}", err or "")
        return Response(html, status=409, mimetype="text/html")

    if is_json_request():
        return jsonify({"ok": True, "message": "User registered."}), 201

    return Response(SUCCESS_HTML, mimetype="text/html")


@app.post("/api/register")
def api_register() -> Response:
    data = request.get_json(silent=True) or {}
    username = data.get("username", "")
    email = data.get("email", "")
    password = data.get("password", "")

    errors = validate_registration(username, email, password)
    if errors:
        return json_error("Validation failed.", 400, errors)

    ok, err = create_user(username, email, password)
    if not ok:
        return json_error(err or "Registration failed.", 409)

    return jsonify({"ok": True, "message": "User registered."}), 201


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)