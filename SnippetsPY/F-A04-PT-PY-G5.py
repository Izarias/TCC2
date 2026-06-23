from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from flask import Flask, jsonify, request
from werkzeug.security import check_password_hash, generate_password_hash


DB_PATH = "app.db"


# -----------------------------
# Errors
# -----------------------------
class AppError(Exception):
    status_code = 400

    def __init__(self, message: str, *, status_code: Optional[int] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.details = details or {}


class ValidationError(AppError):
    status_code = 422


class ConflictError(AppError):
    status_code = 409


class UnauthorizedError(AppError):
    status_code = 401


# -----------------------------
# DTOs
# -----------------------------
@dataclass(frozen=True)
class RegisterInput:
    username: str
    email: str
    password: str


@dataclass(frozen=True)
class PublicUser:
    id: int
    username: str
    email: str
    created_at: str


# -----------------------------
# Validation
# -----------------------------
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")


def _as_str(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def validate_register_payload(payload: Any) -> RegisterInput:
    if not isinstance(payload, dict):
        raise ValidationError("Corpo da requisição deve ser um JSON objeto.")

    username = _as_str(payload.get("username")).strip()
    email = _as_str(payload.get("email")).strip().lower()
    password = _as_str(payload.get("password"))

    errors: Dict[str, str] = {}

    if not username:
        errors["username"] = "Campo obrigatório."
    elif not (3 <= len(username) <= 30):
        errors["username"] = "Deve ter entre 3 e 30 caracteres."
    elif not re.fullmatch(r"[A-Za-z0-9_\.]+", username):
        errors["username"] = "Use apenas letras, números, '_' e '.'."

    if not email:
        errors["email"] = "Campo obrigatório."
    elif len(email) > 254:
        errors["email"] = "E-mail muito longo."
    elif not _EMAIL_RE.match(email):
        errors["email"] = "E-mail inválido."

    if not password:
        errors["password"] = "Campo obrigatório."
    elif len(password) < 8:
        errors["password"] = "Deve ter no mínimo 8 caracteres."
    elif len(password) > 128:
        errors["password"] = "Senha muito longa."

    if errors:
        raise ValidationError("Dados inválidos.", details=errors)

    return RegisterInput(username=username, email=email, password=password)


# -----------------------------
# Persistence
# -----------------------------
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                email TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);
            """
        )


class UserRepository:
    def create_user(self, *, username: str, email: str, password_hash: str) -> PublicUser:
        created_at = datetime.now(timezone.utc).isoformat()
        try:
            with get_db() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO users (username, email, password_hash, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (username, email, password_hash, created_at),
                )
                user_id = int(cur.lastrowid)
        except sqlite3.IntegrityError as e:
            msg = str(e).lower()
            if "idx_users_username" in msg or "users.username" in msg or "username" in msg:
                raise ConflictError("Nome de usuário já está em uso.", details={"field": "username"})
            if "idx_users_email" in msg or "users.email" in msg or "email" in msg:
                raise ConflictError("E-mail já está em uso.", details={"field": "email"})
            raise ConflictError("Conflito ao cadastrar usuário.")
        except sqlite3.Error:
            raise AppError("Erro ao persistir dados.", status_code=500)

        return PublicUser(id=user_id, username=username, email=email, created_at=created_at)

    def find_by_email(self, email: str) -> Optional[sqlite3.Row]:
        try:
            with get_db() as conn:
                row = conn.execute("SELECT * FROM users WHERE email = ? LIMIT 1", (email,)).fetchone()
                return row
        except sqlite3.Error:
            raise AppError("Erro ao consultar dados.", status_code=500)

    def list_public_users(self, *, limit: int = 50, offset: int = 0) -> list[PublicUser]:
        limit = max(1, min(int(limit), 200))
        offset = max(0, int(offset))
        try:
            with get_db() as conn:
                rows = conn.execute(
                    """
                    SELECT id, username, email, created_at
                    FROM users
                    ORDER BY id DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                ).fetchall()
        except sqlite3.Error:
            raise AppError("Erro ao consultar dados.", status_code=500)

        return [
            PublicUser(
                id=int(r["id"]),
                username=str(r["username"]),
                email=str(r["email"]),
                created_at=str(r["created_at"]),
            )
            for r in rows
        ]


# -----------------------------
# Service layer
# -----------------------------
class UserService:
    def __init__(self, repo: UserRepository) -> None:
        self.repo = repo

    def register(self, data: RegisterInput) -> PublicUser:
        password_hash = generate_password_hash(data.password)
        return self.repo.create_user(username=data.username, email=data.email, password_hash=password_hash)

    def authenticate(self, *, email: str, password: str) -> PublicUser:
        email = _as_str(email).strip().lower()
        password = _as_str(password)
        if not email or not password:
            raise ValidationError("E-mail e senha são obrigatórios.", details={"email": "obrigatório", "password": "obrigatório"})

        row = self.repo.find_by_email(email)
        if not row or not check_password_hash(row["password_hash"], password):
            raise UnauthorizedError("Credenciais inválidas.")

        return PublicUser(
            id=int(row["id"]),
            username=str(row["username"]),
            email=str(row["email"]),
            created_at=str(row["created_at"]),
        )


# -----------------------------
# Web app (Flask)
# -----------------------------
app = Flask(__name__)
init_db()

repo = UserRepository()
service = UserService(repo)


@app.errorhandler(AppError)
def handle_app_error(err: AppError):
    payload: Dict[str, Any] = {"error": err.message}
    if getattr(err, "details", None):
        payload["details"] = err.details
    return jsonify(payload), err.status_code


@app.errorhandler(404)
def handle_404(_):
    return jsonify({"error": "Rota não encontrada."}), 404


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.post("/register")
def register():
    payload = request.get_json(silent=True)
    data = validate_register_payload(payload)
    user = service.register(data)
    return jsonify({"user": user.__dict__}), 201


@app.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    user = service.authenticate(email=payload.get("email"), password=payload.get("password"))
    return jsonify({"user": user.__dict__}), 200


@app.get("/users")
def list_users():
    limit = request.args.get("limit", 50)
    offset = request.args.get("offset", 0)
    users = repo.list_public_users(limit=int(limit), offset=int(offset))
    return jsonify({"users": [u.__dict__ for u in users]}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)