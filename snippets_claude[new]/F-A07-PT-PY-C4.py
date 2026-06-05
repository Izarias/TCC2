from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Simulando um banco de dados simples
users_db = {
    "user1": {
        "name": "João Silva",
        "email": "joao@example.com",
        "password": generate_password_hash("senha123")
    }
}

@app.route('/update-password', methods=['PUT'])
def update_password():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Dados inválidos"}), 400
    
    user_id = data.get("user_id")
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if not all([user_id, current_password, new_password]):
        return jsonify({"error": "Campos obrigatórios faltando"}), 400
    
    if user_id not in users_db:
        return jsonify({"error": "Usuário não encontrado"}), 404
    
    user = users_db[user_id]
    
    if not check_password_hash(user["password"], current_password):
        return jsonify({"error": "Senha atual incorreta"}), 401
    
    if len(new_password) < 6:
        return jsonify({"error": "Nova senha deve ter no mínimo 6 caracteres"}), 400
    
    user["password"] = generate_password_hash(new_password)
    
    return jsonify({
        "message": "Senha atualizada com sucesso",
        "user_id": user_id,
        "name": user["name"]
    }), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)