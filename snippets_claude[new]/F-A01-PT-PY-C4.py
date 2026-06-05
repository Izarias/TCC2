from flask import Flask, jsonify, request

app = Flask(__name__)

# Mock data de pedidos
orders = {
    "1": {
        "orderId": "1",
        "customerName": "João Silva",
        "product": "Notebook",
        "quantity": 1,
        "price": 3500.00,
        "status": "Entregue",
        "orderDate": "2026-05-20"
    },
    "2": {
        "orderId": "2",
        "customerName": "Maria Santos",
        "product": "Mouse",
        "quantity": 2,
        "price": 45.00,
        "status": "Processando",
        "orderDate": "2026-06-04"
    },
    "3": {
        "orderId": "3",
        "customerName": "Pedro Costa",
        "product": "Teclado",
        "quantity": 1,
        "price": 150.00,
        "status": "Pendente",
        "orderDate": "2026-06-05"
    }
}

@app.route('/orders/<orderId>', methods=['GET'])
def get_order(orderId):
    order = orders.get(orderId)
    
    if order is None:
        return jsonify({"error": "Pedido não encontrado"}), 404
    
    return jsonify(order), 200

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)