from flask import Flask, request, jsonify

app = Flask(__name__)

users = {
    "john": {"password": "secure123"},
    "jane": {"password": "password456"}
}

@app.route('/update-password', methods=['POST'])
def update_password():
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Request body is required"}), 400
    
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    
    if not username or not old_password or not new_password:
        return jsonify({"error": "Missing required fields"}), 400
    
    if username not in users:
        return jsonify({"error": "User not found"}), 404
    
    if users[username]['password'] != old_password:
        return jsonify({"error": "Invalid current password"}), 401
    
    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    
    users[username]['password'] = new_password
    return jsonify({"message": "Password updated successfully"}), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)