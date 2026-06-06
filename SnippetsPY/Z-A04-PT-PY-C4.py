from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat()
        }

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    return len(password) >= 6

@app.route('/api/users/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not all(key in data for key in ['name', 'email', 'password']):
        return jsonify({'error': 'Nome, email e senha são obrigatórios'}), 400
    
    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    if not name or len(name) < 2:
        return jsonify({'error': 'Nome deve ter pelo menos 2 caracteres'}), 400
    
    if not validate_email(email):
        return jsonify({'error': 'Email inválido'}), 400
    
    if not validate_password(password):
        return jsonify({'error': 'Senha deve ter pelo menos 6 caracteres'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email já cadastrado'}), 409
    
    hashed_password = generate_password_hash(password)
    new_user = User(name=name, email=email, password=hashed_password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({
            'message': 'Usuário registrado com sucesso',
            'user': new_user.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao registrar usuário'}), 500

@app.route('/api/users/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not all(key in data for key in ['email', 'password']):
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400
    
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    user = User.query.filter_by(email=email).first()
    
    if not user or not check_password_hash(user.password, password):
        return jsonify({'error': 'Email ou senha inválidos'}), 401
    
    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict()
    }), 200

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    return jsonify(user.to_dict()), 200

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        name = data.get('name', '').strip()
        if not name or len(name) < 2:
            return jsonify({'error': 'Nome deve ter pelo menos 2 caracteres'}), 400
        user.name = name
    
    if 'email' in data:
        email = data.get('email', '').strip()
        if not validate_email(email):
            return jsonify({'error': 'Email inválido'}), 400
        if User.query.filter_by(email=email).filter(User.id != user_id).first():
            return jsonify({'error': 'Email já cadastrado'}), 409
        user.email = email
    
    if 'password' in data:
        password = data.get('password', '')
        if not validate_password(password):
            return jsonify({'error': 'Senha deve ter pelo menos 6 caracteres'}), 400
        user.password = generate_password_hash(password)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Usuário atualizado com sucesso',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao atualizar usuário'}), 500

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    try:
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Erro ao deletar usuário'}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)