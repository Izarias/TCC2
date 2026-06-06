from flask import Flask, request, jsonify

app = Flask(__name__)

orders = {
    1: {"orderId": 1, "customer": "John Doe", "total": 150.00, "status": "completed"},
    2: {"orderId": 2, "customer": "Jane Smith", "total": 275.50, "status": "pending"},
    3: {"orderId": 3, "customer": "Bob Johnson", "total": 89.99, "status": "shipped"},
}

@app.route('/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = orders.get(order_id)
    
    if order:
        return jsonify(order), 200
    else:
        return jsonify({"error": "Order not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)