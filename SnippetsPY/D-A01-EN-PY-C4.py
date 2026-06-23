from flask import Flask, jsonify, request

app = Flask(__name__)

orders = {
    "1": {"orderId": "1", "customer": "Alice", "product": "Laptop", "amount": 999.99},
    "2": {"orderId": "2", "customer": "Bob", "product": "Mouse", "amount": 29.99},
    "3": {"orderId": "3", "customer": "Charlie", "product": "Keyboard", "amount": 79.99},
}

@app.route('/order/<orderId>', methods=['GET'])
def get_order(orderId):
    order = orders.get(orderId)
    if order:
        return jsonify(order), 200
    return jsonify({"error": "Order not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)