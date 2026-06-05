from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# In-memory user storage (demo purposes)
users = {
    "user1": {
        "password": generate_password_hash("password123"),
        "email": "user1@example.com"
    }
}

@app.route('/update-password', methods=['POST'])
def update_password():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not all([username, old_password, new_password]):
        return jsonify({"error": "Missing required fields"}), 400
    
    if username not in users:
        return jsonify({"error": "User not found"}), 404
    
    if not check_password_hash(users[username]['password'], old_password):
        return jsonify({"error": "Invalid old password"}), 401
    
    if len(new_password) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400
    
    users[username]['password'] = generate_password_hash(new_password)
    
    return jsonify({"message": "Password updated successfully"}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)