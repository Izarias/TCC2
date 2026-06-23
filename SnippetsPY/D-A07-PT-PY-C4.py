from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
DB_FILE = 'users.db'

def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      ('user1', generate_password_hash('old_password')))
        conn.commit()
        conn.close()

def get_user(username):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    return result

def update_password(username, new_password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    hashed = generate_password_hash(new_password)
    cursor.execute("UPDATE users SET password = ? WHERE username = ?",
                  (hashed, username))
    conn.commit()
    conn.close()

@app.route('/update-password', methods=['POST'])
def update_password_endpoint():
    data = request.get_json()
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not all([username, old_password, new_password]):
        return jsonify({'error': 'Missing fields'}), 400

    user = get_user(username)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    if not check_password_hash(user[1], old_password):
        return jsonify({'error': 'Invalid password'}), 401

    update_password(username, new_password)
    return jsonify({'message': 'Password updated successfully'}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)