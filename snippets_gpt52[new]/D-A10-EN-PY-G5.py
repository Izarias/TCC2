#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.error
import urllib.request


def fetch_json(url: str, timeout: float = 10.0) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "lean-api-client/1.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read().decode(charset)
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        raise RuntimeError(f"HTTP {e.code} {e.reason} for {url}\n{body}".rstrip()) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error for {url}: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from {url}: {e}") from e


def summarize_repo(repo_json: dict) -> dict:
    return {
        "full_name": repo_json.get("full_name") or "<unknown>",
        "description": (repo_json.get("description") or "").strip() or "<none>",
        "stars": int(repo_json.get("stargazers_count") or 0),
        "forks": int(repo_json.get("forks_count") or 0),
        "open_issues": int(repo_json.get("open_issues_count") or 0),
        "language": repo_json.get("language") or "<unknown>",
        "license": (repo_json.get("license") or {}).get("spdx_id") or "<none>",
        "url": repo_json.get("html_url") or "<unknown>",
    }


def format_summary(summary: dict) -> str:
    return "\n".join(
        [
            f"Repository:  {summary['full_name']}",
            f"URL:         {summary['url']}",
            f"Description: {summary['description']}",
            f"Language:    {summary['language']}",
            f"License:     {summary['license']}",
            f"Stars:       {summary['stars']:,}",
            f"Forks:       {summary['forks']:,}",
            f"Open issues: {summary['open_issues']:,}",
        ]
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Query GitHub's public API and summarize a repository.")
    p.add_argument(
        "repo",
        nargs="?",
        default="python/cpython",
        help="Repository in owner/name form (default: python/cpython)",
    )
    p.add_argument("--timeout", type=float, default=10.0, help="Request timeout in seconds (default: 10)")
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if "/" not in args.repo or args.repo.count("/") != 1:
        print("Error: repo must be in 'owner/name' format", file=sys.stderr)
        return 2

    url = f"https://api.github.com/repos/{args.repo}"
    try:
        repo_json = fetch_json(url, timeout=args.timeout)
        summary = summarize_repo(repo_json)
        print(format_summary(summary))
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))