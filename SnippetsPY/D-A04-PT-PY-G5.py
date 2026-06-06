#!/usr/bin/env python3
import json
import logging
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import pbkdf2_hmac
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

LOGGER = logging.getLogger("user-registry")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,30}$")

DB_PATH = os.environ.get("USER_DB_PATH", "users.db")
PBKDF2_ITERS = int(os.environ.get("PBKDF2_ITERS", "200000"))
SALT_LEN = 16


@dataclass(frozen=True)
class AppError(Exception):
    status: int
    message: str
    code: str = "error"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def open_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db() -> None:
    conn = open_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                pw_salt BLOB NOT NULL,
                pw_hash BLOB NOT NULL,
                pw_iters INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);")
    finally:
        conn.close()


def read_json_body(handler: BaseHTTPRequestHandler, max_bytes: int = 32_768) -> Dict[str, Any]:
    ctype = (handler.headers.get("Content-Type") or "").split(";")[0].strip().lower()
    if ctype != "application/json":
        raise AppError(415, "Content-Type deve ser application/json", "unsupported_media_type")

    length_raw = handler.headers.get("Content-Length")
    if not length_raw:
        raise AppError(400, "Corpo da requisição ausente", "missing_body")
    try:
        length = int(length_raw)
    except ValueError:
        raise AppError(400, "Content-Length inválido", "invalid_content_length")

    if length < 1:
        raise AppError(400, "Corpo da requisição ausente", "missing_body")
    if length > max_bytes:
        raise AppError(413, "Corpo da requisição muito grande", "payload_too_large")

    raw = handler.rfile.read(length)
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise AppError(400, "JSON inválido", "invalid_json")

    if not isinstance(data, dict):
        raise AppError(400, "JSON deve ser um objeto", "invalid_json_shape")
    return data


def normalize_username(username: Any) -> str:
    if not isinstance(username, str):
        raise AppError(400, "username deve ser string", "invalid_username")
    username = username.strip()
    if not USERNAME_RE.fullmatch(username):
        raise AppError(400, "username inválido (3-30, A-Z a-z 0-9 _)", "invalid_username")
    return username


def normalize_email(email: Any) -> str:
    if not isinstance(email, str):
        raise AppError(400, "email deve ser string", "invalid_email")
    email = email.strip().lower()
    if len(email) > 254 or not EMAIL_RE.fullmatch(email):
        raise AppError(400, "email inválido", "invalid_email")
    return email


def validate_password(password: Any) -> str:
    if not isinstance(password, str):
        raise AppError(400, "password deve ser string", "invalid_password")
    if len(password) < 8 or len(password) > 128:
        raise AppError(400, "password inválida (8-128 caracteres)", "invalid_password")
    has_letter = any(c.isalpha() for c in password)
    has_digit = any(c.isdigit() for c in password)
    if not (has_letter and has_digit):
        raise AppError(400, "password deve conter letras e números", "weak_password")
    return password


def hash_password(password: str, iters: int = PBKDF2_ITERS) -> Tuple[bytes, bytes, int]:
    if iters < 100_000:
        iters = 100_000
    salt = os.urandom(SALT_LEN)
    pw_hash = pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
    return salt, pw_hash, iters


def create_user(username: str, email: str, password: str) -> Dict[str, Any]:
    salt, pw_hash, iters = hash_password(password)
    created_at = utc_now_iso()

    conn = open_db()
    try:
        try:
            cur = conn.execute(
                """
                INSERT INTO users (username, email, pw_salt, pw_hash, pw_iters, created_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (username, email, sqlite3.Binary(salt), sqlite3.Binary(pw_hash), iters, created_at),
            )
        except sqlite3.IntegrityError as e:
            msg = str(e).lower()
            if "users.username" in msg:
                raise AppError(409, "username já está em uso", "username_taken")
            if "users.email" in msg:
                raise AppError(409, "email já está em uso", "email_taken")
            raise AppError(409, "conflito ao criar usuário", "conflict")

        user_id = cur.lastrowid
        return {"id": user_id, "username": username, "email": email, "created_at": created_at}
    finally:
        conn.close()


class Handler(BaseHTTPRequestHandler):
    server_version = "UserRegistry/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        LOGGER.info("%s - %s", self.address_string(), fmt % args)

    def send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def handle_exception(self, e: Exception) -> None:
        if isinstance(e, AppError):
            self.send_json(e.status, {"ok": False, "error": {"code": e.code, "message": e.message}})
            return
        LOGGER.exception("Unhandled error")
        self.send_json(500, {"ok": False, "error": {"code": "internal_error", "message": "erro interno"}})

    def do_GET(self) -> None:
        try:
            if self.path == "/health":
                self.send_json(200, {"ok": True, "status": "up"})
                return
            self.send_json(404, {"ok": False, "error": {"code": "not_found", "message": "rota não encontrada"}})
        except Exception as e:
            self.handle_exception(e)

    def do_POST(self) -> None:
        try:
            if self.path != "/register":
                self.send_json(404, {"ok": False, "error": {"code": "not_found", "message": "rota não encontrada"}})
                return

            data = read_json_body(self)
            username = normalize_username(data.get("username"))
            email = normalize_email(data.get("email"))
            password = validate_password(data.get("password"))

            user = create_user(username=username, email=email, password=password)
            self.send_json(201, {"ok": True, "user": user})
        except Exception as e:
            self.handle_exception(e)


def run(host: str, port: int) -> None:
    init_db()
    httpd = ThreadingHTTPServer((host, port), Handler)
    LOGGER.info("Listening on http://%s:%d", host, port)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


def parse_args(argv: list) -> Tuple[str, int]:
    host = os.environ.get("HOST", "127.0.0.1")
    port_s = os.environ.get("PORT", "8000")
    if len(argv) >= 2:
        host = argv[1]
    if len(argv) >= 3:
        port_s = argv[2]
    try:
        port = int(port_s)
    except ValueError:
        raise SystemExit("PORT inválida")
    if not (1 <= port <= 65535):
        raise SystemExit("PORT fora do intervalo")
    return host, port


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    h, p = parse_args(sys.argv)
    run(h, p)