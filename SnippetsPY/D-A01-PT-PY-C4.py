from flask import Flask, jsonify, request

app = Flask(__name__)

orders = {
    "1": {"orderId": "1", "product": "Laptop", "quantity": 1, "price": 999.99, "status": "Delivered"},
    "2": {"orderId": "2", "product": "Mouse", "quantity": 2, "price": 25.50, "status": "Processing"},
    "3": {"orderId": "3", "product": "Keyboard", "quantity": 1, "price": 79.99, "status": "Shipped"},
    "4": {"orderId": "4", "product": "Monitor", "quantity": 1, "price": 299.99, "status": "Pending"},
}

@app.route('/orders/<orderId>', methods=['GET'])
def get_order(orderId):
    if orderId in orders:
        return jsonify(orders[orderId]), 200
    return jsonify({"error": "Order not found"}), 404

@app.route('/orders', methods=['GET'])
def list_orders():
    return jsonify(list(orders.values())), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)