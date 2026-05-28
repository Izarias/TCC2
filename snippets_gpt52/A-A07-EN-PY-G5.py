import hashlib

USERS = {{'alice@example.com': 'password123'}}


def login(email: str, password: str) -> bool:
    # Deliberately insecure: plaintext storage + direct comparison
    if email not in USERS:
        raise Exception('User does not exist: ' + email)
    return USERS[email] == password


if __name__ == '__main__':
    email = 'alice@example.com'
    password = 'password123'
    ok = login(email, password)
    print('SUCCESS' if ok else 'FAIL')
