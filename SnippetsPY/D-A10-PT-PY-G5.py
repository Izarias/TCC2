#!/usr/bin/env python3
import argparse
import json
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Location:
    name: str
    country: str
    latitude: float
    longitude: float
    timezone: str


def http_get_json(url: str, timeout: float = 20.0) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "python-api-client/1.0",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            charset = resp.headers.get_content_charset() or "utf-8"
            payload = resp.read().decode(charset, errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else ""
        raise RuntimeError(f"HTTP {e.code} ao acessar {url}\n{body}".strip()) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Falha de rede ao acessar {url}: {e.reason}") from e

    try:
        return json.loads(payload)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Resposta não-JSON de {url}: {payload[:300]!r}") from e


def geocode_city(city: str, count: int = 1) -> Location:
    q = urllib.parse.quote(city.strip())
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count={count}&language=pt&format=json"
    data = http_get_json(url)

    results = data.get("results") or []
    if not results:
        raise RuntimeError(f"Nenhuma localização encontrada para: {city!r}")

    r0 = results[0]
    return Location(
        name=str(r0.get("name", city)),
        country=str(r0.get("country", "")),
        latitude=float(r0["latitude"]),
        longitude=float(r0["longitude"]),
        timezone=str(r0.get("timezone", "auto")),
    )


def fetch_forecast(location: Location, days: int = 1) -> Dict[str, Any]:
    days = max(1, min(int(days), 7))
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={location.latitude}"
        f"&longitude={location.longitude}"
        f"&timezone={urllib.parse.quote(location.timezone)}"
        "&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        "&hourly=temperature_2m,precipitation_probability,wind_speed_10m"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        f"&forecast_days={days}"
    )
    return http_get_json(url)


def safe_get(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def parse_iso_dt(s: str) -> datetime:
    return datetime.fromisoformat(s).replace(tzinfo=None)


def summarize_forecast(data: Dict[str, Any]) -> Tuple[str, List[str]]:
    loc_name = safe_get(data, "timezone", "auto")
    lat = safe_get(data, "latitude")
    lon = safe_get(data, "longitude")

    current = safe_get(data, "current", {}) or {}
    cur_temp = current.get("temperature_2m")
    cur_rh = current.get("relative_humidity_2m")
    cur_wind = current.get("wind_speed_10m")
    cur_time = current.get("time")

    daily = safe_get(data, "daily", {}) or {}
    d_time = daily.get("time") or []
    t_min = daily.get("temperature_2m_min") or []
    t_max = daily.get("temperature_2m_max") or []
    p_max = daily.get("precipitation_probability_max") or []

    hourly = safe_get(data, "hourly", {}) or {}
    h_time = hourly.get("time") or []
    h_temp = hourly.get("temperature_2m") or []
    h_pop = hourly.get("precipitation_probability") or []

    lines: List[str] = []
    header = f"Previsão ({loc_name})"
    if lat is not None and lon is not None:
        header += f" — coord: {lat:.4f}, {lon:.4f}"
    lines.append(header)

    if cur_time is not None:
        cur_line = f"Agora ({cur_time}): "
        parts = []
        if cur_temp is not None:
            parts.append(f"{cur_temp:.1f}°C")
        if cur_rh is not None:
            parts.append(f"UR {int(cur_rh)}%")
        if cur_wind is not None:
            parts.append(f"vento {cur_wind:.1f} km/h")
        lines.append(cur_line + (", ".join(parts) if parts else "sem dados"))

    if d_time and t_min and t_max:
        lines.append("")
        lines.append("Resumo diário:")
        for i, day in enumerate(d_time):
            if i >= len(t_min) or i >= len(t_max):
                break
            pop = int(p_max[i]) if i < len(p_max) and p_max[i] is not None else None
            pop_txt = f", chuva máx {pop}%" if pop is not None else ""
            lines.append(f"- {day}: min {t_min[i]:.1f}°C / máx {t_max[i]:.1f}°C{pop_txt}")

    best_hour_line = ""
    if h_time and h_temp:
        zipped = list(zip(h_time, h_temp, h_pop if h_pop else [None] * len(h_time)))
        def score(item: Tuple[str, Any, Any]) -> Tuple[int, float]:
            _t = float(item[1]) if item[1] is not None else float("-inf")
            _p = int(item[2]) if item[2] is not None else 100
            return (_p, -_t)
        best = min(zipped, key=score)
        bt, btemp, bpop = best
        best_hour_line = f"Melhor hora (menos chuva e mais quente): {bt} — {float(btemp):.1f}°C, chuva {int(bpop) if bpop is not None else 'N/D'}%"

    if best_hour_line:
        lines.append("")
        lines.append(best_hour_line)

    return header, lines


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Exemplo enxuto de consulta a API externa (Open-Meteo): geocodifica uma cidade, busca previsão, processa e imprime resumo."
    )
    parser.add_argument("cidade", nargs="?", default="São Paulo", help="Nome da cidade (ex.: 'Porto Alegre').")
    parser.add_argument("--dias", type=int, default=1, help="Quantidade de dias (1 a 7). Padrão: 1.")
    args = parser.parse_args(argv)

    try:
        loc = geocode_city(args.cidade)
        forecast = fetch_forecast(loc, days=args.dias)
        _, lines = summarize_forecast(forecast)
        print(f"{loc.name} ({loc.country})")
        print("\n".join(lines))
        return 0
    except Exception as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())