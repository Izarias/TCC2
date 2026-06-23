from flask import Flask, jsonify, request

app = Flask(__name__)

# Mock order database
orders = {
    "001": {"orderId": "001", "customer": "John Doe", "total": 150.50, "status": "Completed"},
    "002": {"orderId": "002", "customer": "Jane Smith", "total": 200.00, "status": "Pending"},
    "003": {"orderId": "003", "customer": "Bob Wilson", "total": 75.25, "status": "Shipped"},
    "004": {"orderId": "004", "customer": "Alice Brown", "total": 320.00, "status": "Processing"},
}

@app.route('/orders/<orderId>', methods=['GET'])
def get_order(orderId):
    if orderId in orders:
        return jsonify(orders[orderId]), 200
    else:
        return jsonify({"error": "Order not found"}), 404

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)