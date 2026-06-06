#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def fetch_json(
    url: str,
    *,
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 15.0,
) -> Any:
    if params:
        parsed = urllib.parse.urlsplit(url)
        existing = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        merged = existing + list(params.items())
        new_query = urllib.parse.urlencode(merged, doseq=True)
        url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, new_query, parsed.fragment))

    req_headers = {
        "Accept": "application/json",
        "User-Agent": "api-client-python/1.0",
    }
    if headers:
        req_headers.update(headers)

    req = urllib.request.Request(url, headers=req_headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read().decode(charset, errors="replace")

            if "application/json" in content_type.lower() or raw.lstrip().startswith(("{", "[")):
                return json.loads(raw)
            return {"content_type": content_type, "text": raw}

    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
            try:
                detail = json.loads(body)
            except json.JSONDecodeError:
                detail = body
        except Exception:
            detail = None
        raise RuntimeError(f"HTTP {e.code} {e.reason} for {url}", detail) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error for {url}: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Response was not valid JSON for {url}: {e}") from e


def print_result(data: Any, *, pretty: bool = True) -> None:
    if pretty:
        print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(json.dumps(data, ensure_ascii=False))


def parse_kv_pairs(pairs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"Invalid KEY=VALUE pair: {item!r}")
        k, v = item.split("=", 1)
        k = k.strip()
        if not k:
            raise ValueError(f"Invalid KEY=VALUE pair (empty key): {item!r}")
        out[k] = v
    return out


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Query an external API, parse JSON, and display the result.")
    p.add_argument(
        "url",
        nargs="?",
        default="https://api.github.com",
        help="API URL to query (default: https://api.github.com)",
    )
    p.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Query string parameter (repeatable).",
    )
    p.add_argument(
        "--header",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="HTTP header (repeatable).",
    )
    p.add_argument("--timeout", type=float, default=15.0, help="Request timeout in seconds.")
    p.add_argument("--raw", action="store_true", help="Print compact JSON (no pretty formatting).")
    args = p.parse_args(argv)

    try:
        params = parse_kv_pairs(args.param)
        headers = parse_kv_pairs(args.header)
        data = fetch_json(args.url, params=params or None, headers=headers or None, timeout=args.timeout)
        print_result(data, pretty=not args.raw)
        return 0
    except Exception as e:
        if isinstance(e, RuntimeError) and len(e.args) >= 2:
            msg, detail = e.args[0], e.args[1]
            print(f"Error: {msg}", file=sys.stderr)
            if detail is not None:
                try:
                    print(json.dumps(detail, indent=2, ensure_ascii=False, sort_keys=True), file=sys.stderr)
                except Exception:
                    print(str(detail), file=sys.stderr)
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))