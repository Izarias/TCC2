#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

DB_PATH = os.environ.get("APP_DB_PATH", "users.db")
HOST = os.environ.get("APP_HOST", "127.0.0.1")
PORT = int(os.environ.get("APP_PORT", "8000"))

PBKDF2_ALG = "sha256"
PBKDF2_ITERS = int(os.environ.get("APP_PBKDF2_ITERS", "210000"))
SALT_BYTES = 16
DK_LEN = 32

MIN_PASSWORD_LEN = int(os.environ.get("APP_MIN_PASSWORD_LEN", "8"))


def b64e(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def b64d(txt: str) -> bytes:
    return base64.b64decode(txt.encode("ascii"), validate=True)


def password_hash(password: str, *, salt: bytes, iterations: int) -> bytes:
    return hashlib.pbkdf2_hmac(PBKDF2_ALG, password.encode("utf-8"), salt, iterations, dklen=DK_LEN)


def ensure_db() -> None:
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                salt_b64 TEXT NOT NULL,
                iterations INTEGER NOT NULL,
                hash_b64 TEXT NOT NULL
            )
            """
        )
        con.commit()


def get_user(username: str):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute(
            "SELECT username, salt_b64, iterations, hash_b64 FROM users WHERE username = ?",
            (username,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "username": row[0],
            "salt_b64": row[1],
            "iterations": int(row[2]),
            "hash_b64": row[3],
        }


def upsert_user_password(username: str, new_password: str) -> None:
    salt = secrets.token_bytes(SALT_BYTES)
    iterations = PBKDF2_ITERS
    dk = password_hash(new_password, salt=salt, iterations=iterations)
    with sqlite3.connect(DB_PATH) as con:
        con.execute(
            """
            INSERT INTO users (username, salt_b64, iterations, hash_b64)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                salt_b64=excluded.salt_b64,
                iterations=excluded.iterations,
                hash_b64=excluded.hash_b64
            """,
            (username, b64e(salt), iterations, b64e(dk)),
        )
        con.commit()


def verify_password(username: str, password: str) -> bool:
    user = get_user(username)
    if not user:
        return False
    try:
        salt = b64d(user["salt_b64"])
        stored = b64d(user["hash_b64"])
        iterations = int(user["iterations"])
    except Exception:
        return False
    computed = password_hash(password, salt=salt, iterations=iterations)
    return hmac.compare_digest(stored, computed)


def validate_new_password(new_password: str) -> str | None:
    if not isinstance(new_password, str):
        return "new_password deve ser uma string"
    if len(new_password) < MIN_PASSWORD_LEN:
        return f"new_password deve ter pelo menos {MIN_PASSWORD_LEN} caracteres"
    if new_password.strip() != new_password:
        return "new_password não deve começar/terminar com espaços"
    return None


class Handler(BaseHTTPRequestHandler):
    server_version = "SimplePwdApp/1.0"

    def _send_json(self, status: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = self.headers.get("Content-Length")
        if not length:
            raise ValueError("Corpo ausente")
        try:
            n = int(length)
        except ValueError:
            raise ValueError("Content-Length inválido")
        if n <= 0 or n > 1024 * 1024:
            raise ValueError("Tamanho do corpo inválido")
        raw = self.rfile.read(n)
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            raise ValueError("JSON inválido")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health":
            return self._send_json(200, {"ok": True})
        return self._send_json(404, {"error": "not_found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/password/update":
            try:
                data = self._read_json()
            except ValueError as e:
                return self._send_json(400, {"error": "bad_request", "message": str(e)})

            username = data.get("username")
            old_password = data.get("old_password")
            new_password = data.get("new_password")

            if not isinstance(username, str) or not username.strip():
                return self._send_json(400, {"error": "bad_request", "message": "username é obrigatório"})
            if not isinstance(old_password, str):
                return self._send_json(400, {"error": "bad_request", "message": "old_password é obrigatório"})
            msg = validate_new_password(new_password)
            if msg:
                return self._send_json(400, {"error": "bad_request", "message": msg})

            # Resposta genérica para credenciais inválidas (evita enumeração simples).
            if not verify_password(username, old_password):
                return self._send_json(401, {"error": "unauthorized", "message": "credenciais inválidas"})

            upsert_user_password(username, new_password)
            return self._send_json(200, {"ok": True})

        return self._send_json(404, {"error": "not_found"})

    def log_message(self, format, *args):
        # Log simples para stderr
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))


def bootstrap_demo_user():
    demo_user = os.environ.get("APP_DEMO_USER", "alice")
    demo_pass = os.environ.get("APP_DEMO_PASS", "Password123!")
    if get_user(demo_user) is None:
        upsert_user_password(demo_user, demo_pass)


def main():
    ensure_db()
    bootstrap_demo_user()
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Servidor em http://{HOST}:{PORT}")
    print("Endpoints:")
    print("  GET  /health")
    print("  POST /password/update  JSON: {username, old_password, new_password}")
    httpd.serve_forever()


if __name__ == "__main__":
    main()