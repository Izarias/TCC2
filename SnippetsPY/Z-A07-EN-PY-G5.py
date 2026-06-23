from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory "database"
users = {
    1: {"username": "alice", "password": "alice123"},
    2: {"username": "bob", "password": "bob123"}
}

@app.route("/users/<int:user_id>/password", methods=["PUT"])
def update_password(user_id):
    if user_id not in users:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if not data or "newPassword" not in data:
        return jsonify({"error": "newPassword is required"}), 400

    new_password = data["newPassword"]
    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    users[user_id]["password"] = new_password

    return jsonify({
        "message": "Password updated successfully",
        "userId": user_id
    }), 200

if __name__ == "__main__":
    app.run(debug=True)