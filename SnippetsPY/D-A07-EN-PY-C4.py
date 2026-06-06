from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

@app.route('/update-password', methods=['POST'])
def update_password():
    data = request.get_json()
    
    if not data or 'user_id' not in data or 'new_password' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    user_id = data['user_id']
    new_password = data['new_password']
    
    users = load_users()
    
    if user_id not in users:
        return jsonify({'error': 'User not found'}), 404
    
    users[user_id]['password'] = new_password
    users[user_id]['last_updated'] = datetime.now().isoformat()
    
    save_users(users)
    
    return jsonify({'message': 'Password updated successfully'}), 200

if __name__ == '__main__':
    if not os.path.exists(USERS_FILE):
        initial_users = {
            'user1': {'username': 'john_doe', 'password': 'old_password', 'email': 'john@example.com'},
            'user2': {'username': 'jane_smith', 'password': 'secure_pass', 'email': 'jane@example.com'}
        }
        save_users(initial_users)
    
    app.run(debug=True, port=5000)