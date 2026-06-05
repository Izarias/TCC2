from __future__ import annotations

import base64
import hmac
import os
import re
from dataclasses import dataclass
from hashlib import pbkdf2_hmac
from typing import Dict, Optional, Tuple

from flask import Flask, jsonify, request

app = Flask(__name__)


# ----------------------------
# "Database" (in-memory)
# ----------------------------

@dataclass
class User:
    id: str
    password_salt_b64: str
    password_hash_b64: str
    password_iterations: int


USERS: Dict[str, User] = {}


# ----------------------------
# Security helpers
# ----------------------------

PBKDF2_ALG = "sha256"
PBKDF2_ITERATIONS = 210_000
SALT_BYTES = 16
HASH_BYTES = 32


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64d(text: str) -> bytes:
    pad = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode((text + pad).encode("ascii"))


def hash_password(password: str, *, salt: Optional[bytes] = None, iterations: int = PBKDF2_ITERATIONS) -> Tuple[str, str, int]:
    if salt is None:
        salt = os.urandom(SALT_BYTES)
    digest = pbkdf2_hmac(PBKDF2_ALG, password.encode("utf-8"), salt, iterations, dklen=HASH_BYTES)
    return _b64e(salt), _b64e(digest), iterations


def verify_password(password: str, *, salt_b64: str, hash_b64: str, iterations: int) -> bool:
    salt = _b64d(salt_b64)
    expected = _b64d(hash_b64)
    actual = pbkdf2_hmac(PBKDF2_ALG, password.encode("utf-8"), salt, iterations, dklen=len(expected))
    return hmac.compare_digest(actual, expected)


def validate_new_password(new_password: str) -> Optional[str]:
    if not isinstance(new_password, str) or not new_password:
        return "A nova senha é obrigatória."
    if len(new_password) < 10:
        return "A nova senha deve ter pelo menos 10 caracteres."
    if len(new_password) > 128:
        return "A nova senha deve ter no máximo 128 caracteres."
    if not re.search(r"[a-z]", new_password):
        return "A nova senha deve conter ao menos uma letra minúscula."
    if not re.search(r"[A-Z]", new_password):
        return "A nova senha deve conter ao menos uma letra maiúscula."
    if not re.search(r"\d", new_password):
        return "A nova senha deve conter ao menos um número."
    if not re.search(r"[^\w\s]", new_password):
        return "A nova senha deve conter ao menos um caractere especial."
    return None


# ----------------------------
# Setup sample user
# ----------------------------

def seed_users() -> None:
    salt_b64, hash_b64, iters = hash_password("Senha@12345")
    USERS["1"] = User(
        id="1",
        password_salt_b64=salt_b64,
        password_hash_b64=hash_b64,
        password_iterations=iters,
    )


seed_users()


# ----------------------------
# Routes
# ----------------------------

@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.post("/users/<user_id>/password")
def update_password(user_id: str):
    user = USERS.get(user_id)
    if user is None:
        return jsonify({"error": "Usuário não encontrado."}), 404

    payload = request.get_json(silent=True) or {}
    current_password = payload.get("current_password")
    new_password = payload.get("new_password")

    if not isinstance(current_password, str) or not current_password:
        return jsonify({"error": "A senha atual é obrigatória."}), 400
    if not isinstance(new_password, str) or not new_password:
        return jsonify({"error": "A nova senha é obrigatória."}), 400

    if not verify_password(
        current_password,
        salt_b64=user.password_salt_b64,
        hash_b64=user.password_hash_b64,
        iterations=user.password_iterations,
    ):
        return jsonify({"error": "Senha atual inválida."}), 401

    pwd_error = validate_new_password(new_password)
    if pwd_error:
        return jsonify({"error": pwd_error}), 400

    if current_password == new_password:
        return jsonify({"error": "A nova senha deve ser diferente da senha atual."}), 400

    salt_b64, hash_b64, iters = hash_password(new_password)
    user.password_salt_b64 = salt_b64
    user.password_hash_b64 = hash_b64
    user.password_iterations = iters

    return jsonify({"message": "Senha atualizada com sucesso."}), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)