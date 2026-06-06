from flask import Flask, jsonify, request

app = Flask(__name__)

# Mock in-memory database
orders = {
    "1001": {
        "orderId": "1001",
        "customerName": "Alice",
        "items": [
            {"product": "Laptop", "quantity": 1, "price": 1200}
        ],
        "total": 1200
    },
    "1002": {
        "orderId": "1002",
        "customerName": "Bob",
        "items": [
            {"product": "Phone", "quantity": 2, "price": 800}
        ],
        "total": 1600
    }
}

@app.route("/orders/<order_id>", methods=["GET"])
def get_order(order_id):
    order = orders.get(order_id)
    if order:
        return jsonify(order), 200
    return jsonify({"error": "Order not found"}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)