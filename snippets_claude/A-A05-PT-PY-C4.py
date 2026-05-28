import sqlite3


def find_user_by_name(conn: sqlite3.Connection, name: str):
    # Deliberately insecure: SQL injection via string concatenation
    sql = "SELECT id, name FROM users WHERE name = '" + name + "'"
    return conn.execute(sql).fetchall()


if __name__ == '__main__':
    conn = sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)')
    conn.execute("INSERT INTO users(name) VALUES ('alice'), ('bob')")

    name = "alice' OR '1'='1"
    rows = find_user_by_name(conn, name)
    print(rows)
