from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from typing import Optional

from flask import Flask, flash, g, redirect, render_template_string, request, session, url_for

APP_SECRET = os.environ.get("APP_SECRET", os.urandom(32))
DB_PATH = os.environ.get("DB_PATH", "app.db")

PBKDF2_ITERS = int(os.environ.get("PBKDF2_ITERS", "210000"))
SALT_BYTES = 16
DK_LEN = 32


def b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def b64d(txt: str) -> bytes:
    pad = "=" * (-len(txt) % 4)
    return base64.urlsafe_b64decode((txt + pad).encode("ascii"))


def hash_password(password: str) -> str:
    salt = os.urandom(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERS, dklen=DK_LEN)
    return f"pbkdf2_sha256${PBKDF2_ITERS}${b64e(salt)}${b64e(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, iters_s, salt_s, dk_s = stored.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iters = int(iters_s)
        salt = b64d(salt_s)
        expected = b64d(dk_s)
    except Exception:
        return False

    got = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters, dklen=len(expected))
    return hmac.compare_digest(got, expected)


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_email(email: str) -> Optional[str]:
    email = email.strip().lower()
    if not email:
        return "E-mail é obrigatório."
    if len(email) > 254:
        return "E-mail é muito longo."
    if not EMAIL_RE.match(email):
        return "E-mail inválido."
    return None


def validate_password(password: str) -> Optional[str]:
    if not password:
        return "Senha é obrigatória."
    if len(password) < 8:
        return "Senha deve ter no mínimo 8 caracteres."
    if len(password) > 256:
        return "Senha é muito longa."
    return None


app = Flask(__name__)
app.secret_key = APP_SECRET
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_exc: object | None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db() -> None:
    db = get_db()
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        """
    )
    db.commit()


@dataclass(frozen=True)
class User:
    id: int
    email: str
    name: str
    created_at: int


def current_user() -> Optional[User]:
    uid = session.get("user_id")
    if not isinstance(uid, int):
        return None
    db = get_db()
    row = db.execute("SELECT id, email, name, created_at FROM users WHERE id = ?", (uid,)).fetchone()
    if row is None:
        return None
    return User(id=row["id"], email=row["email"], name=row["name"], created_at=row["created_at"])


BASE_HTML = """
<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>{{ title }}</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:720px;margin:40px auto;padding:0 16px;line-height:1.35}
    .nav{display:flex;gap:12px;align-items:center;margin-bottom:18px}
    .nav a{color:#0a58ca;text-decoration:none}
    .card{border:1px solid #ddd;border-radius:12px;padding:18px}
    label{display:block;margin-top:10px}
    input{width:100%;padding:10px;border:1px solid #bbb;border-radius:10px;margin-top:6px}
    button{margin-top:14px;padding:10px 14px;border:0;border-radius:10px;background:#0a58ca;color:#fff;cursor:pointer}
    .flash{background:#fff3cd;border:1px solid #ffeeba;border-radius:10px;padding:10px;margin:10px 0}
    .muted{color:#666;font-size:0.95em}
    .row{display:flex;gap:10px;flex-wrap:wrap}
    .row > div{flex:1;min-width:240px}
  </style>
</head>
<body>
  <div class="nav">
    <a href="{{ url_for('index') }}">Início</a>
    {% if user %}
      <a href="{{ url_for('me') }}">Minha conta</a>
      <a href="{{ url_for('logout') }}">Sair</a>
    {% else %}
      <a href="{{ url_for('register') }}">Cadastrar</a>
      <a href="{{ url_for('login') }}">Entrar</a>
    {% endif %}
  </div>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for m in messages %}
        <div class="flash">{{ m }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}

  <div class="card">
    {{ body|safe }}
  </div>
</body>
</html>
"""


@app.before_request
def _ensure_db() -> None:
    init_db()


@app.get("/")
def index():
    user = current_user()
    body = """
      <h1>Aplicação simples</h1>
      {% if user %}
        <p>Você está logado como <strong>{{ user.name }}</strong> ({{ user.email }}).</p>
        <p class="muted">Use "Minha conta" para ver seus dados.</p>
      {% else %}
        <p>Faça cadastro ou login para continuar.</p>
      {% endif %}
    """
    return render_template_string(BASE_HTML, title="Início", user=user, body=render_template_string(body, user=user))


@app.get("/register")
def register():
    user = current_user()
    if user:
        return redirect(url_for("me"))

    body = """
      <h1>Cadastro</h1>
      <form method="post" action="{{ url_for('register_post') }}" autocomplete="on">
        <div class="row">
          <div>
            <label for="name">Nome</label>
            <input id="name" name="name" required maxlength="80" />
          </div>
          <div>
            <label for="email">E-mail</label>
            <input id="email" name="email" type="email" required maxlength="254" />
          </div>
        </div>

        <label for="password">Senha</label>
        <input id="password" name="password" type="password" required minlength="8" maxlength="256" />

        <button type="submit">Criar conta</button>
      </form>
      <p class="muted">Já tem conta? <a href="{{ url_for('login') }}">Entrar</a>.</p>
    """
    return render_template_string(BASE_HTML, title="Cadastro", user=None, body=body)


@app.post("/register")
def register_post():
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if not name:
        flash("Nome é obrigatório.")
        return redirect(url_for("register"))
    if len(name) > 80:
        flash("Nome é muito longo.")
        return redirect(url_for("register"))

    err = validate_email(email) or validate_password(password)
    if err:
        flash(err)
        return redirect(url_for("register"))

    db = get_db()
    pw_hash = hash_password(password)
    now = int(time.time())

    try:
        cur = db.execute(
            "INSERT INTO users (email, name, password_hash, created_at) VALUES (?, ?, ?, ?)",
            (email, name, pw_hash, now),
        )
        db.commit()
    except sqlite3.IntegrityError:
        flash("Já existe uma conta com este e-mail.")
        return redirect(url_for("register"))

    session.clear()
    session["user_id"] = int(cur.lastrowid)
    flash("Conta criada com sucesso.")
    return redirect(url_for("me"))


@app.get("/login")
def login():
    user = current_user()
    if user:
        return redirect(url_for("me"))

    body = """
      <h1>Login</h1>
      <form method="post" action="{{ url_for('login_post') }}" autocomplete="on">
        <label for="email">E-mail</label>
        <input id="email" name="email" type="email" required maxlength="254" />

        <label for="password">Senha</label>
        <input id="password" name="password" type="password" required maxlength="256" />

        <button type="submit">Entrar</button>
      </form>
      <p class="muted">Não tem conta? <a href="{{ url_for('register') }}">Cadastrar</a>.</p>
    """
    return render_template_string(BASE_HTML, title="Login", user=None, body=body)


@app.post("/login")
def login_post():
    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    err = validate_email(email)
    if err:
        flash(err)
        return redirect(url_for("login"))
    if not password:
        flash("Senha é obrigatória.")
        return redirect(url_for("login"))

    db = get_db()
    row = db.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,)).fetchone()
    if row is None or not verify_password(password, row["password_hash"]):
        flash("E-mail ou senha inválidos.")
        return redirect(url_for("login"))

    session.clear()
    session["user_id"] = int(row["id"])
    flash("Login realizado.")
    return redirect(url_for("me"))


@app.get("/logout")
def logout():
    session.clear()
    flash("Você saiu.")
    return redirect(url_for("index"))


@app.get("/me")
def me():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    body = """
      <h1>Minha conta</h1>
      <p><strong>Nome:</strong> {{ user.name }}</p>
      <p><strong>E-mail:</strong> {{ user.email }}</p>
      <p class="muted"><strong>Criada em:</strong> {{ created }}</p>

      <hr style="border:0;border-top:1px solid #ddd;margin:14px 0" />

      <h2>Alterar senha</h2>
      <form method="post" action="{{ url_for('change_password') }}">
        <label for="current_password">Senha atual</label>
        <input id="current_password" name="current_password" type="password" required maxlength="256" />

        <label for="new_password">Nova senha</label>
        <input id="new_password" name="new_password" type="password" required minlength="8" maxlength="256" />

        <button type="submit">Atualizar senha</button>
      </form>
    """
    created = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(user.created_at))
    return render_template_string(
        BASE_HTML,
        title="Minha conta",
        user=user,
        body=render_template_string(body, user=user, created=created),
    )


@app.post("/me/change-password")
def change_password():
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    current_password = request.form.get("current_password") or ""
    new_password = request.form.get("new_password") or ""

    err = validate_password(new_password)
    if err:
        flash(err)
        return redirect(url_for("me"))

    db = get_db()
    row = db.execute("SELECT password_hash FROM users WHERE id = ?", (user.id,)).fetchone()
    if row is None or not verify_password(current_password, row["password_hash"]):
        flash("Senha atual incorreta.")
        return redirect(url_for("me"))

    db.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user.id))
    db.commit()
    flash("Senha atualizada.")
    return redirect(url_for("me"))


if __name__ == "__main__":
    # Dependência: pip install flask
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5000")), debug=True)