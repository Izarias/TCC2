from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory "database"
users = {
    1: {"username": "alice", "password": "oldpassword1"},
    2: {"username": "bob", "password": "oldpassword2"}
}

@app.route("/users/<int:user_id>/password", methods=["PUT"])
def update_password(user_id):
    data = request.get_json()
    if not data or "new_password" not in data:
        return jsonify({"error": "new_password is required"}), 400

    user = users.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    user["password"] = data["new_password"]
    users[user_id] = user  # Persist change in the in-memory store

    return jsonify({"message": "Password updated successfully"}), 200

if __name__ == "__main__":
    app.run(debug=True)