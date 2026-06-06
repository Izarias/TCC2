import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def fetch_json(url: str, timeout: int = 15, headers: dict | None = None) -> object:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "python-urllib/1.0",
            **(headers or {}),
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        raw = resp.read().decode(charset, errors="replace")
        return json.loads(raw)


def main() -> int:
    url = "https://api.coindesk.com/v1/bpi/currentprice/BTC.json"

    try:
        data = fetch_json(url)
    except urllib.error.HTTPError as e:
        print(f"Erro HTTP: {e.code} - {e.reason}", file=sys.stderr)
        return 2
    except urllib.error.URLError as e:
        print(f"Erro de rede: {e.reason}", file=sys.stderr)
        return 3
    except json.JSONDecodeError as e:
        print(f"Resposta não é JSON válido: {e}", file=sys.stderr)
        return 4
    except Exception as e:
        print(f"Erro inesperado: {e}", file=sys.stderr)
        return 1

    updated = data.get("time", {}).get("updatedISO") or data.get("time", {}).get("updated")
    usd = data.get("bpi", {}).get("USD", {})
    brl = data.get("bpi", {}).get("BRL", {})

    print("Resultado da API (Coindesk - BTC):")
    if updated:
        print(f"Atualizado em: {updated}")
    if usd:
        print(f"USD: {usd.get('rate')} ({usd.get('code')})")
    if brl:
        print(f"BRL: {brl.get('rate')} ({brl.get('code')})")

    if not (usd or brl):
        print(json.dumps(data, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())