import sqlite3
import re
from bcrypt import hashpw, gensalt, checkpw
from datetime import datetime


class UserRegistrationError(Exception):
    pass


class UserAlreadyExistsError(UserRegistrationError):
    pass


class ValidationError(UserRegistrationError):
    pass


class Database:
    def __init__(self, db_path='users.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def user_exists(self, username, email):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM users WHERE username = ? OR email = ?', (username, email))
            return cursor.fetchone() is not None

    def save_user(self, username, email, password_hash):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    'INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                    (username, email, password_hash)
                )
                conn.commit()
            except sqlite3.IntegrityError as e:
                raise UserAlreadyExistsError(f"Username or email already exists: {str(e)}")

    def get_user(self, username):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, email, password_hash FROM users WHERE username = ?', (username,))
            return cursor.fetchone()


class UserValidator:
    MIN_USERNAME_LENGTH = 3
    MAX_USERNAME_LENGTH = 20
    MIN_PASSWORD_LENGTH = 8
    EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    @staticmethod
    def validate_username(username):
        if not username or not isinstance(username, str):
            raise ValidationError("Username must be a non-empty string")
        
        if len(username) < UserValidator.MIN_USERNAME_LENGTH or len(username) > UserValidator.MAX_USERNAME_LENGTH:
            raise ValidationError(f"Username must be between {UserValidator.MIN_USERNAME_LENGTH} and {UserValidator.MAX_USERNAME_LENGTH} characters")
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError("Username can only contain letters, numbers, hyphens, and underscores")

    @staticmethod
    def validate_email(email):
        if not email or not isinstance(email, str):
            raise ValidationError("Email must be a non-empty string")
        
        if not re.match(UserValidator.EMAIL_REGEX, email):
            raise ValidationError("Invalid email format")

    @staticmethod
    def validate_password(password):
        if not password or not isinstance(password, str):
            raise ValidationError("Password must be a non-empty string")
        
        if len(password) < UserValidator.MIN_PASSWORD_LENGTH:
            raise ValidationError(f"Password must be at least {UserValidator.MIN_PASSWORD_LENGTH} characters")
        
        if not any(c.isupper() for c in password):
            raise ValidationError("Password must contain at least one uppercase letter")
        
        if not any(c.isdigit() for c in password):
            raise ValidationError("Password must contain at least one digit")


class UserRegistration:
    def __init__(self, db_path='users.db'):
        self.db = Database(db_path)

    def register(self, username, email, password):
        try:
            username = username.strip() if username else ""
            email = email.strip().lower() if email else ""
            
            UserValidator.validate_username(username)
            UserValidator.validate_email(email)
            UserValidator.validate_password(password)
            
            if self.db.user_exists(username, email):
                raise UserAlreadyExistsError("Username or email already registered")
            
            password_hash = hashpw(password.encode('utf-8'), gensalt())
            self.db.save_user(username, email, password_hash)
            
            return {"success": True, "message": f"User '{username}' registered successfully"}
        
        except UserRegistrationError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def login(self, username, password):
        try:
            user = self.db.get_user(username)
            if not user:
                return {"success": False, "error": "Invalid credentials"}
            
            user_id, stored_username, email, password_hash = user
            if checkpw(password.encode('utf-8'), password_hash):
                return {"success": True, "message": "Login successful", "user_id": user_id, "email": email}
            else:
                return {"success": False, "error": "Invalid credentials"}
        
        except Exception as e:
            return {"success": False, "error": f"Login error: {str(e)}"}


if __name__ == "__main__":
    registration = UserRegistration()
    
    print("=== User Registration System ===\n")
    
    test_cases = [
        ("john_doe", "john@example.com", "SecurePass123"),
        ("alice", "alice@example.com", "ValidPass456"),
        ("bob", "bob@example.com", "short"),
        ("bob", "invalid-email", "ValidPass789"),
        ("john_doe", "different@example.com", "AnotherPass123"),
    ]
    
    for username, email, password in test_cases:
        print(f"Registering: {username}, {email}")
        result = registration.register(username, email, password)
        print(f"Result: {result}\n")
    
    print("\n=== Login Test ===\n")
    
    login_result = registration.login("john_doe", "SecurePass123")
    print(f"Login john_doe with correct password: {login_result}")
    
    login_result = registration.login("john_doe", "WrongPassword123")
    print(f"Login john_doe with wrong password: {login_result}")