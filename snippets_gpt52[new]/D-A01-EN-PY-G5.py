from flask import Flask, request, jsonify

app = Flask(__name__)

# Mock data source
ORDERS = {
    "1001": {"orderId": "1001", "customer": "Alice", "items": ["Book", "Pen"], "total": 29.90},
    "1002": {"orderId": "1002", "customer": "Bob", "items": ["Notebook"], "total": 9.90},
    "1003": {"orderId": "1003", "customer": "Charlie", "items": ["Laptop", "Mouse"], "total": 1200.00},
}

@app.route("/orders", methods=["GET"])
def get_order():
    order_id = request.args.get("orderId")

    if not order_id:
        return jsonify({"error": "orderId parameter is required"}), 400

    order = ORDERS.get(order_id)

    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify(order), 200

if __name__ == "__main__":
    app.run(debug=True)