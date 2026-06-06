from flask import Flask, jsonify, request

app = Flask(__name__)

# Mock database (in-memory)
ORDERS = {
    "1001": {
        "orderId": "1001",
        "status": "PROCESSING",
        "currency": "BRL",
        "total": 199.90,
        "items": [
            {"sku": "SKU-001", "name": "Produto A", "qty": 1, "unitPrice": 99.95},
            {"sku": "SKU-002", "name": "Produto B", "qty": 1, "unitPrice": 99.95},
        ],
        "customer": {"id": "CUST-10", "name": "Ana Souza"},
    },
    "1002": {
        "orderId": "1002",
        "status": "SHIPPED",
        "currency": "BRL",
        "total": 59.90,
        "items": [
            {"sku": "SKU-003", "name": "Produto C", "qty": 2, "unitPrice": 29.95},
        ],
        "customer": {"id": "CUST-11", "name": "Bruno Lima"},
    },
}


@app.get("/order")
def get_order_details():
    order_id = request.args.get("orderId", type=str)
    if not order_id:
        return jsonify({"error": "Missing required query parameter: orderId"}), 400

    order = ORDERS.get(order_id)
    if not order:
        return jsonify({"error": "Order not found", "orderId": order_id}), 404

    return jsonify(order), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)