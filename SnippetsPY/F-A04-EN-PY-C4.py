import re
import sqlite3
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
DATABASE = 'users.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

class ValidationError(Exception):
    pass

class UserValidator:
    @staticmethod
    def validate_username(username):
        if not username or len(username) < 3:
            raise ValidationError("Username must be at least 3 characters long")
        if len(username) > 20:
            raise ValidationError("Username must not exceed 20 characters")
        if not re.match("^[a-zA-Z0-9_]+$", username):
            raise ValidationError("Username can only contain letters, numbers, and underscores")
        return True

    @staticmethod
    def validate_email(email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Invalid email format")
        return True

    @staticmethod
    def validate_password(password):
        if not password or len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long")
        if not re.search("[a-z]", password):
            raise ValidationError("Password must contain at least one lowercase letter")
        if not re.search("[A-Z]", password):
            raise ValidationError("Password must contain at least one uppercase letter")
        if not re.search("[0-9]", password):
            raise ValidationError("Password must contain at least one digit")
        return True

class UserRepository:
    @staticmethod
    def user_exists(username=None, email=None):
        conn = get_db()
        cursor = conn.cursor()
        if username:
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        if email:
            cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
            result = cursor.fetchone()
            conn.close()
            return result is not None
        return False

    @staticmethod
    def create_user(username, email, password):
        password_hash = generate_password_hash(password)
        conn = get_db()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                (username, email, password_hash)
            )
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return {"id": user_id, "username": username, "email": email}
        except sqlite3.IntegrityError:
            conn.close()
            raise ValidationError("Username or email already exists")

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        UserValidator.validate_username(username)
        UserValidator.validate_email(email)
        UserValidator.validate_password(password)
        
        if UserRepository.user_exists(username=username):
            return jsonify({"error": "Username already taken"}), 409
        if UserRepository.user_exists(email=email):
            return jsonify({"error": "Email already registered"}), 409
        
        user = UserRepository.create_user(username, email, password)
        return jsonify({"message": "User registered successfully", "user": user}), 201
    
    except ValidationError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"error": "Username and password required"}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not check_password_hash(user['password_hash'], password):
            return jsonify({"error": "Invalid username or password"}), 401
        
        return jsonify({"message": "Login successful", "user_id": user['id']}), 200
    
    except Exception as e:
        return jsonify({"error": "Login failed"}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)