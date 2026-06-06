from flask import Flask, jsonify, request

app = Flask(__name__)

# In-memory mock data for demonstration purposes
ORDERS = {
    "1001": {
        "orderId": "1001",
        "customerName": "Alice Johnson",
        "items": [
            {"productId": "P001", "name": "Laptop", "quantity": 1, "price": 1200.00},
            {"productId": "P002", "name": "Mouse", "quantity": 2, "price": 25.00}
        ],
        "totalAmount": 1250.00,
        "status": "Shipped"
    },
    "1002": {
        "orderId": "1002",
        "customerName": "Bob Smith",
        "items": [
            {"productId": "P003", "name": "Keyboard", "quantity": 1, "price": 75.00}
        ],
        "totalAmount": 75.00,
        "status": "Processing"
    }
}

@app.route("/orders", methods=["GET"])
def get_order():
    # Retrieve orderId from query parameters
    order_id = request.args.get("orderId")

    if not order_id:
        return jsonify({"error": "orderId parameter is required"}), 400

    # Lookup order details
    order = ORDERS.get(order_id)

    if not order:
        return jsonify({"error": f"Order with id {order_id} not found"}), 404

    # Return order details
    return jsonify(order), 200


if __name__ == "__main__":
    app.run(debug=True)