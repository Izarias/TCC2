#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.error
import urllib.request


def fetch_json(url: str, timeout: float = 15.0) -> object:
    headers = {
        "Accept": "application/json",
        "User-Agent": "api-client-demo/1.0 (+https://example.invalid)",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        content_type = (resp.headers.get("Content-Type") or "").lower()
        raw = resp.read()
        if "application/json" not in content_type:
            try:
                return json.loads(raw.decode("utf-8", errors="replace"))
            except json.JSONDecodeError:
                return {"_raw_text": raw.decode("utf-8", errors="replace")}
        return json.loads(raw.decode("utf-8"))


def pretty_print(data: object) -> None:
    print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Query an external API and display returned data.")
    parser.add_argument(
        "url",
        nargs="?",
        default="https://api.github.com/repos/python/cpython",
        help="API URL to query (default: GitHub CPython repo metadata).",
    )
    parser.add_argument("--timeout", type=float, default=15.0, help="Request timeout in seconds.")
    args = parser.parse_args()

    try:
        data = fetch_json(args.url, timeout=args.timeout)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        print(f"HTTP error: {e.code} {e.reason}", file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
        return 2
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        return 3
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Failed to parse response as JSON: {e}", file=sys.stderr)
        return 4
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1

    pretty_print(data)

    if isinstance(data, dict) and args.url.startswith("https://api.github.com/"):
        name = data.get("full_name") or data.get("name")
        stars = data.get("stargazers_count")
        forks = data.get("forks_count")
        open_issues = data.get("open_issues_count")
        if any(v is not None for v in (name, stars, forks, open_issues)):
            print("\nSummary:")
            if name is not None:
                print(f"- Repo: {name}")
            if stars is not None:
                print(f"- Stars: {stars}")
            if forks is not None:
                print(f"- Forks: {forks}")
            if open_issues is not None:
                print(f"- Open issues: {open_issues}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())