import re
import sqlite3

NAME_RE = re.compile(r"^[A-Za-z0-9_\- ]{1,50}$")


def find_user_by_name(conn: sqlite3.Connection, name: str):
    if not name or not NAME_RE.match(name):
        raise ValueError('Invalid name')

    sql = "SELECT id, name FROM users WHERE name = ?"
    return conn.execute(sql, (name,)).fetchall()


def setup_db() -> sqlite3.Connection:
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)')
    conn.executemany('INSERT INTO users(name) VALUES (?)', [('alice',), ('bob',)])
    return conn


if __name__ == '__main__':
    conn = setup_db()
    try:
        print(find_user_by_name(conn, 'alice'))
        # Example of rejected input
        # find_user_by_name(conn, "alice' OR 1=1 --")
    finally:
        conn.close()
