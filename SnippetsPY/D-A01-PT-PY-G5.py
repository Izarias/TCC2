from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, List

from flask import Flask, jsonify, request

app = Flask(__name__)


@dataclass(frozen=True)
class OrderItem:
    sku: str
    name: str
    unit_price: str  # string para evitar float (ex.: "19.90")
    quantity: int


@dataclass(frozen=True)
class Order:
    order_id: str
    customer_name: str
    currency: str
    created_at: str  # ISO-8601
    status: str
    items: List[OrderItem]


# "Base de dados" em memória para o exemplo.
ORDERS: Dict[str, Order] = {
    "1001": Order(
        order_id="1001",
        customer_name="Ana Silva",
        currency="BRL",
        created_at="2026-06-01T10:15:00Z",
        status="PAID",
        items=[
            OrderItem(sku="SKU-001", name="Camiseta", unit_price="59.90", quantity=1),
            OrderItem(sku="SKU-010", name="Caneca", unit_price="29.90", quantity=2),
        ],
    ),
    "1002": Order(
        order_id="1002",
        customer_name="Bruno Souza",
        currency="BRL",
        created_at="2026-06-03T18:42:00Z",
        status="CREATED",
        items=[OrderItem(sku="SKU-777", name="Mouse", unit_price="149.90", quantity=1)],
    ),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _calculate_totals(order: Order) -> dict:
    subtotal = Decimal("0")
    total_items = 0

    for it in order.items:
        unit = Decimal(it.unit_price)
        line_total = unit * it.quantity
        subtotal += line_total
        total_items += it.quantity

    tax = (subtotal * Decimal("0.00")).quantize(Decimal("0.01"))
    shipping = Decimal("0.00")
    total = (subtotal + tax + shipping).quantize(Decimal("0.01"))

    return {
        "subtotal": str(subtotal.quantize(Decimal("0.01"))),
        "tax": str(tax),
        "shipping": str(shipping.quantize(Decimal("0.01"))),
        "total": str(total),
        "totalItems": total_items,
    }


@app.get("/orders")
def get_order_details():
    order_id = (request.args.get("orderId") or "").strip()
    if not order_id:
        return jsonify(
            {
                "error": "missing_parameter",
                "message": "Informe o parâmetro 'orderId' na query string.",
                "timestamp": _now_iso(),
            }
        ), 400

    order = ORDERS.get(order_id)
    if not order:
        return jsonify(
            {
                "error": "not_found",
                "message": f"Pedido não encontrado para orderId='{order_id}'.",
                "timestamp": _now_iso(),
            }
        ), 404

    payload = asdict(order)
    payload["items"] = [asdict(i) for i in order.items]
    payload["summary"] = _calculate_totals(order)
    payload["timestamp"] = _now_iso()
    return jsonify(payload), 200


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)