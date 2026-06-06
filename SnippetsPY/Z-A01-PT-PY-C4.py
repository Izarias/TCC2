from flask import Flask, jsonify, request

app = Flask(__name__)

# Base de dados simulada
orders = {
    1: {"orderId": 1, "customerName": "João Silva", "product": "Notebook", "quantity": 1, "price": 3500.00, "status": "Entregue"},
    2: {"orderId": 2, "customerName": "Maria Santos", "product": "Mouse", "quantity": 2, "price": 50.00, "status": "Processando"},
    3: {"orderId": 3, "customerName": "Pedro Costa", "product": "Teclado", "quantity": 1, "price": 200.00, "status": "Pendente"},
}

@app.route('/order/<int:order_id>', methods=['GET'])
def get_order(order_id):
    order = orders.get(order_id)
    if order:
        return jsonify(order), 200
    else:
        return jsonify({"error": "Pedido não encontrado"}), 404

@app.route('/orders', methods=['GET'])
def get_all_orders():
    return jsonify(list(orders.values())), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)