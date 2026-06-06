# app.py
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import re
from datetime import datetime

app = Flask(__name__)

# Database setup
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

# Validation
def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 6:
        return False, "Senha deve ter no mínimo 6 caracteres"
    if not any(char.isdigit() for char in password):
        return False, "Senha deve conter pelo menos um número"
    if not any(char.isalpha() for char in password):
        return False, "Senha deve conter pelo menos uma letra"
    return True, ""

def validate_user_data(name, email, password):
    errors = []
    
    if not name or len(name.strip()) < 3:
        errors.append("Nome deve ter no mínimo 3 caracteres")
    
    if not email or not validate_email(email):
        errors.append("Email inválido")
    
    is_valid, msg = validate_password(password)
    if not is_valid:
        errors.append(msg)
    
    return errors

# Routes
@app.route('/api/users/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validate input
        errors = validate_user_data(name, email, password)
        if errors:
            return jsonify({'errors': errors}), 400
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        # Save to database
        conn = get_db()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
                (name, email, hashed_password)
            )
            conn.commit()
            user_id = cursor.lastrowid
            
            return jsonify({
                'message': 'Usuário cadastrado com sucesso',
                'user_id': user_id,
                'email': email
            }), 201
        
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email já cadastrado'}), 409
        
        finally:
            conn.close()
    
    except Exception as e:
        return jsonify({'error': 'Erro ao processar requisição'}), 500

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, email, created_at FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        return jsonify({
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'created_at': user['created_at']
        }), 200
    
    except Exception as e:
        return jsonify({'error': 'Erro ao recuperar usuário'}), 500

@app.route('/api/users/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email e senha são obrigatórios'}), 400
        
        email = data.get('email').strip()
        password = data.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, password FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'error': 'Email ou senha inválidos'}), 401
        
        return jsonify({
            'message': 'Login realizado com sucesso',
            'user_id': user['id'],
            'name': user['name']
        }), 200
    
    except Exception as e:
        return jsonify({'error': 'Erro ao realizar login'}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)