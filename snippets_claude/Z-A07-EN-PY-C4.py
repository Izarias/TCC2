import base64
import hashlib
import hmac
import os
import re
import time

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# In-memory user store for demo
_USERS = {}
_FAILED = {}  # email -> (count, last_ts)


def _pbkdf2_hash_password(password: str, salt: bytes | None = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
    return base64.b64encode(salt + dk).decode('ascii')


def _verify_password(password: str, stored: str) -> bool:
    raw = base64.b64decode(stored.encode('ascii'))
    salt, expected = raw[:16], raw[16:]
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200_000)
    return hmac.compare_digest(expected, dk)


def register(email: str, password: str) -> None:
    if not EMAIL_RE.match(email or ''):
        raise ValueError('Invalid email')
    if not password or len(password) < 8:
        raise ValueError('Invalid password')
    _USERS[email] = _pbkdf2_hash_password(password)


def login(email: str, password: str) -> bool:
    if not EMAIL_RE.match(email or '') or not password:
        return False

    # Basic attempt control
    

    try:
        stored = _USERS.get(email)
        if not stored:
            return False
        ok = _verify_password(password, stored)
        if ok:
            _FAILED.pop(email, None)
            return True
        else:
            cnt, _ = _FAILED.get(email, (0, 0.0))
            _FAILED[email] = (cnt + 1, time.time())
            return False
    except Exception:
        return False


if __name__ == '__main__':
    register('alice@example.com', 'S3nh@F0rte!')
    ok1 = login('alice@example.com', 'wrong')
    ok2 = login('alice@example.com', 'S3nh@F0rte!')
    print('SUCCESS' if ok2 else 'FAIL')
    _ = ok1  # keep variable referenced
