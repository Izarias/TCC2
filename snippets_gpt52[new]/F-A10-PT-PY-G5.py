#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple


@dataclass(frozen=True)
class ApiResponse:
    url: str
    status: int
    headers: Dict[str, str]
    data: Any
    raw_text: str


class ApiClient:
    def __init__(self, timeout_seconds: float = 15.0, user_agent: str = "api-client/1.0") -> None:
        self._timeout = timeout_seconds
        self._user_agent = user_agent

    def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> ApiResponse:
        final_url = self._with_params(url, params or {})
        req = urllib.request.Request(final_url, method="GET")
        req.add_header("User-Agent", self._user_agent)
        req.add_header("Accept", "application/json, text/plain, */*")
        for k, v in (headers or {}).items():
            req.add_header(k, v)

        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                status = getattr(resp, "status", 200)
                resp_headers = {k: v for k, v in resp.headers.items()}
                body_bytes = resp.read()
        except urllib.error.HTTPError as e:
            body_bytes = e.read() if hasattr(e, "read") else b""
            status = e.code
            resp_headers = dict(e.headers.items()) if getattr(e, "headers", None) else {}
        except urllib.error.URLError as e:
            raise RuntimeError(f"Falha de rede ao acessar {final_url}: {e.reason}") from e

        raw_text = body_bytes.decode("utf-8", errors="replace")
        data = self._try_parse_json(raw_text)

        return ApiResponse(
            url=final_url,
            status=status,
            headers=resp_headers,
            data=data,
            raw_text=raw_text,
        )

    @staticmethod
    def _with_params(url: str, params: Dict[str, str]) -> str:
        if not params:
            return url
        parts = urllib.parse.urlsplit(url)
        existing = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
        merged = existing + list(params.items())
        new_query = urllib.parse.urlencode(merged, doseq=True)
        return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, new_query, parts.fragment))

    @staticmethod
    def _try_parse_json(text: str) -> Any:
        try:
            return json.loads(text)
        except Exception:
            return text


def parse_kv_pairs(items: Iterable[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Parâmetro inválido '{item}'. Use o formato chave=valor.")
        k, v = item.split("=", 1)
        k = k.strip()
        if not k:
            raise ValueError(f"Parâmetro inválido '{item}'. A chave não pode ser vazia.")
        result[k] = v
    return result


def present(response: ApiResponse, *, pretty: bool = True, show_headers: bool = False) -> None:
    print(f"URL: {response.url}")
    print(f"Status: {response.status}")

    if show_headers:
        print("Headers:")
        for k in sorted(response.headers.keys(), key=str.lower):
            print(f"  {k}: {response.headers[k]}")

    print("Resultado:")
    if isinstance(response.data, (dict, list)) and pretty:
        print(json.dumps(response.data, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(response.raw_text)


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Consulta uma API externa via HTTP GET, obtém os dados e apresenta o resultado no console."
    )
    p.add_argument(
        "url",
        nargs="?",
        default="https://jsonplaceholder.typicode.com/todos/1",
        help="URL da API (padrão: JSONPlaceholder).",
    )
    p.add_argument(
        "-p",
        "--param",
        action="append",
        default=[],
        metavar="CHAVE=VALOR",
        help="Parâmetro de query string (pode repetir). Ex.: -p userId=1",
    )
    p.add_argument(
        "-H",
        "--header",
        action="append",
        default=[],
        metavar="CHAVE=VALOR",
        help="Header HTTP (pode repetir). Ex.: -H Authorization=Bearer%20TOKEN",
    )
    p.add_argument("--timeout", type=float, default=15.0, help="Timeout em segundos (padrão: 15).")
    p.add_argument("--no-pretty", action="store_true", help="Não formatar JSON com indentação.")
    p.add_argument("--show-headers", action="store_true", help="Exibir headers da resposta.")
    return p


def main(argv: Optional[Tuple[str, ...]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        params = parse_kv_pairs(args.param)
        headers = parse_kv_pairs(args.header)
    except ValueError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2

    client = ApiClient(timeout_seconds=args.timeout)

    try:
        resp = client.get(args.url, params=params, headers=headers)
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1

    present(resp, pretty=not args.no_pretty, show_headers=args.show_headers)
    return 0 if 200 <= resp.status < 300 else 1


if __name__ == "__main__":
    raise SystemExit(main())