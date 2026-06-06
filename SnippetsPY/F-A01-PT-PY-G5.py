#!/usr/bin/env python3
import json
import os
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

ORDERS = {
    "1001": {
        "orderId": "1001",
        "status": "PAID",
        "customer": {"customerId": "C-10", "name": "Maria Silva"},
        "items": [
            {"sku": "SKU-ABC", "name": "Produto A", "qty": 2, "unitPrice": 19.9},
            {"sku": "SKU-XYZ", "name": "Produto B", "qty": 1, "unitPrice": 49.9},
        ],
    },
    "1002": {
        "orderId": "1002",
        "status": "PENDING",
        "customer": {"customerId": "C-20", "name": "João Souza"},
        "items": [{"sku": "SKU-123", "name": "Produto C", "qty": 3, "unitPrice": 9.9}],
    },
}

ORDER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\-]{0,63}$")


def compute_totals(order: dict) -> dict:
    items = order.get("items", [])
    subtotal = sum((i.get("qty", 0) * i.get("unitPrice", 0.0)) for i in items)
    return {
        **order,
        "totals": {
            "currency": "BRL",
            "subtotal": round(float(subtotal), 2),
            "itemsCount": int(sum(i.get("qty", 0) for i in items)),
        },
    }


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "SimpleOrders/1.0"

    def _send_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error(self, status_code: int, message: str, details: dict | None = None) -> None:
        payload = {"error": {"message": message}}
        if details:
            payload["error"]["details"] = details
        self._send_json(status_code, payload)

    def log_message(self, fmt: str, *args) -> None:
        print("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), fmt % args))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/")

        # Route: GET /orders/<orderId>
        order_id = None
        m = re.match(r"^/orders/([^/]+)$", path)
        if m:
            order_id = m.group(1)

        # Alternative: GET /orders?orderId=<orderId>
        if path == "/orders" and order_id is None:
            qs = parse_qs(parsed.query or "")
            order_id = (qs.get("orderId") or [None])[0]

        if order_id is None:
            self._send_error(
                404,
                "Rota não encontrada",
                {"hint": "Use GET /orders/<orderId> ou GET /orders?orderId=<orderId>"},
            )
            return

        if not ORDER_ID_PATTERN.match(order_id):
            self._send_error(400, "orderId inválido", {"orderId": order_id})
            return

        order = ORDERS.get(order_id)
        if order is None:
            self._send_error(404, "Pedido não encontrado", {"orderId": order_id})
            return

        self._send_json(200, compute_totals(order))


def main() -> None:
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8000"))
    httpd = HTTPServer((host, port), RequestHandler)
    print(f"Servidor iniciado em http://{host}:{port}")
    print("Endpoints:")
    print("  GET /orders/<orderId>")
    print("  GET /orders?orderId=<orderId>")
    httpd.serve_forever()


if __name__ == "__main__":
    main()