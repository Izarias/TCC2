from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'

# Simulated user database
users_db = {
    'user1': {
        'username': 'user1',
        'email': 'user1@example.com',
        'password': generate_password_hash('oldpassword123'),
        'created_at': datetime.now().isoformat()
    }
}


@app.route('/update-password', methods=['POST'])
def update_password():
    """Endpoint to update a user's password"""
    
    # Extract request data
    data = request.get_json()
    
    # Validate required fields
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    username = data.get('username')
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_password = data.get('confirm_password')
    
    # Validate input
    if not all([username, current_password, new_password, confirm_password]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if len(new_password) < 8:
        return jsonify({'error': 'New password must be at least 8 characters'}), 400
    
    if new_password != confirm_password:
        return jsonify({'error': 'Passwords do not match'}), 400
    
    # Check if user exists
    if username not in users_db:
        return jsonify({'error': 'User not found'}), 404
    
    user = users_db[username]
    
    # Verify current password
    if not check_password_hash(user['password'], current_password):
        return jsonify({'error': 'Current password is incorrect'}), 401
    
    # Prevent using same password
    if check_password_hash(user['password'], new_password):
        return jsonify({'error': 'New password must be different from current password'}), 400
    
    # Update password
    user['password'] = generate_password_hash(new_password)
    user['updated_at'] = datetime.now().isoformat()
    
    return jsonify({
        'message': 'Password updated successfully',
        'username': username,
        'updated_at': user['updated_at']
    }), 200


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)