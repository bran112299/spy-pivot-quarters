#!/usr/bin/env python3
"""
Pivot Quarters — one Flask app: static UI + TradingView API (same origin).

Run:  python3 server/app.py
  or: python3 server/pivot_tv_proxy.py

Open: http://127.0.0.1:8787/

Session: POST /api/login with JSON {"cookies": "sessionid=...; ..."}
"""
from __future__ import annotations

import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

# Project root (parent of server/)
_BASE = Path(__file__).resolve().parent.parent
_BASE_STR = str(_BASE)
_TV = os.path.join(_BASE_STR, "tv-dashboard")
if _TV not in sys.path:
    sys.path.insert(0, _TV)

import requests as http
from flask import Flask, abort, jsonify, request, send_from_directory

from domain.time_frames import TimeFrame
from infrastructure.tradingview.authentication.trading_view_session import TradingViewSession
from infrastructure.tradingview.data.trading_view_data_client import TradingViewDataClient
from infrastructure.tradingview.time_frames.time_frame_converter import TradingViewTimeFrameConverter

app = Flask(__name__)

COOKIES_PATH = os.path.join(_TV, "cache", "cookies.pkl")


@app.after_request
def _cors_api(resp):
    """Allow chart UI on another port/host to call /api/* (bars, search, login)."""
    p = request.path or ""
    if p.startswith("/api/"):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.before_request
def _api_preflight():
    if request.method == "OPTIONS" and (request.path or "").startswith("/api/"):
        return ("", 204)
_BASE_PATH = _BASE.resolve()

TF_MINUTES = {
    "1m": 1,
    "3m": 3,
    "15m": 15,
    "1h": 60,
    "4h": 240,
    "8h": 480,
    "1d": 1440,
    "1w": 10080,
    "1M": 43200,
}

TF_TO_DOMAIN = {
    "1m": TimeFrame.TF_1MINUTE,
    "3m": TimeFrame.TF_3MINUTE,
    "15m": TimeFrame.TF_15MINUTE,
    "1h": TimeFrame.TF_1HOUR,
    "4h": TimeFrame.TF_4HOUR,
    "8h": TimeFrame.TF_8HOUR,
    "1d": TimeFrame.TF_1DAY,
    "1w": TimeFrame.TF_1WEEK,
    "1M": TimeFrame.TF_1MONTH,
}

_session_cache = None

TV_SYMBOL_SEARCH_URL = "https://symbol-search.tradingview.com/symbol_search/v3/"
TV_SYMBOL_SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/",
}

_symbol_alias_map_cache: dict | None = None


def _tv_strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s or "").strip()


def _tv_hit_full_symbol(hit: dict) -> str | None:
    sym = _tv_strip_html(str(hit.get("symbol") or "")).upper()
    if not sym:
        return None
    prefix = hit.get("prefix") or hit.get("source_id") or ""
    prefix = str(prefix).strip().upper()
    if not prefix:
        ex = str(hit.get("exchange") or "").strip()
        if ex:
            prefix = re.sub(r"[^A-Z0-9_]+", "", ex.upper())
    if not prefix:
        return None
    return f"{prefix}:{sym}"


def _get_symbol_alias_map() -> dict:
    """UPPER short name -> full TradingView symbol (tv-dashboard/symbols.py)."""
    global _symbol_alias_map_cache
    if _symbol_alias_map_cache is None:
        m: dict[str, str] = {}
        try:
            import symbols as sm

            for name in dir(sm):
                if not name.isupper() or name.startswith("_"):
                    continue
                val = getattr(sm, name, None)
                if isinstance(val, str) and ":" in val:
                    m[name.upper()] = val.upper()
        except ImportError:
            pass
        _symbol_alias_map_cache = m
    return _symbol_alias_map_cache


def _pickle_path():
    return COOKIES_PATH


def cookies_exist():
    return os.path.exists(_pickle_path())


def load_session():
    global _session_cache
    import pickle

    if _session_cache:
        return _session_cache
    with open(_pickle_path(), "rb") as f:
        _session_cache = TradingViewSession.from_dict(pickle.load(f))
    return _session_cache


def save_session(session):
    global _session_cache
    import pickle

    os.makedirs(os.path.dirname(_pickle_path()), exist_ok=True)
    with open(_pickle_path(), "wb") as f:
        pickle.dump(session.to_dict(), f)
    _session_cache = session


def parse_date(s, fallback):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return fallback


def _get_candles(ticker: str, tf_key: str, bars_count: int):
    session = load_session()
    converter = TradingViewTimeFrameConverter()
    client = TradingViewDataClient(
        trading_view_time_frame_converter=converter, verbose=False
    )
    return client.get_data(
        trading_view_session=session,
        ticker=ticker.upper(),
        time_frame=TF_TO_DOMAIN[tf_key],
        bars_count=bars_count,
    )


def _send_project_file(rel: str):
    rel = (rel or "").strip().replace("\\", "/").lstrip("/")
    if not rel:
        rel = "index.html"
    parts = Path(rel).parts
    if ".." in parts:
        abort(404)
    candidate = (_BASE_PATH / rel).resolve()
    try:
        candidate.relative_to(_BASE_PATH)
    except ValueError:
        abort(404)
    if not candidate.is_file():
        abort(404)
    return send_from_directory(str(candidate.parent), candidate.name)


@app.route("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "cookies": cookies_exist(),
            "tv_dashboard": _TV,
        }
    )


@app.route("/api/login", methods=["POST"])
def api_login():
    body = request.get_json() or {}
    cookies = (body.get("cookies") or "").strip()
    if not cookies:
        return jsonify({"error": "cookies are required"}), 400
    m = re.search(r"(?:^|;\s*)sessionid=([^;]+)", cookies)
    if not m:
        return jsonify({"error": "sessionid not found in cookie string"}), 400
    sessionid = m.group(1).strip()
    try:
        resp = http.get(
            "https://www.tradingview.com/",
            headers={
                "Cookie": cookies,
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
                "Referer": "https://www.tradingview.com",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=15,
        )
        auth_token = None
        for pattern in [
            r'"auth_token"\s*:\s*"([^"]+)"',
            r"'auth_token'\s*:\s*'([^']+)'",
            r'auth_token["\s:=]+([A-Za-z0-9._-]{40,})',
        ]:
            m2 = re.search(pattern, resp.text)
            if m2:
                auth_token = m2.group(1)
                break
        if not auth_token:
            return (
                jsonify(
                    {"error": "Could not extract auth token — cookies may be expired."}
                ),
                401,
            )
        session = TradingViewSession(
            session_id=sessionid, auth_token=auth_token, user_id=""
        )
        save_session(session)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/bars")
def api_bars():
    if not cookies_exist():
        return (
            jsonify(
                {
                    "error": "No TV session. POST /api/login with cookies or log in via tv-dashboard once.",
                    "candles": [],
                }
            ),
            401,
        )

    ticker = request.args.get("ticker", "AMEX:SPY").strip()
    tf = request.args.get("tf", "15m").strip()
    if tf not in TF_TO_DOMAIN:
        return jsonify({"error": f"Unsupported tf: {tf}", "candles": []}), 400

    from_date = parse_date(request.args.get("from", ""), date(2024, 1, 1))
    to_date = parse_date(request.args.get("to", ""), date.today())

    mins = TF_MINUTES[tf]
    bars = max(500, int((to_date - from_date).days * 24 * 60 / mins) + 100)
    bars = min(bars, 50_000)

    try:
        candles = _get_candles(ticker, tf, bars)
    except Exception as e:
        return jsonify({"error": str(e), "candles": []}), 500

    from_dt = datetime(from_date.year, from_date.month, from_date.day)
    to_dt = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59)

    out = [
        {
            "time": int(c.open_time.timestamp()),
            "open": round(c.open, 6),
            "high": round(c.high, 6),
            "low": round(c.low, 6),
            "close": round(c.close, 6),
        }
        for c in candles
        if from_dt <= c.open_time <= to_dt
    ]
    out.sort(key=lambda x: x["time"])
    return jsonify({"ok": True, "candles": out, "cached": False})


@app.route("/api/symbol-search")
def api_symbol_search():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"error": "q is required"}), 400
    try:
        limit = min(15, max(1, int(request.args.get("limit", "12"))))
    except ValueError:
        limit = 12

    if ":" in q:
        return jsonify({"results": [], "qualified": True})

    qu = q.upper()
    aliases = _get_symbol_alias_map()
    if qu in aliases:
        fs = aliases[qu]
        return jsonify(
            {
                "results": [
                    {
                        "fullSymbol": fs,
                        "description": qu,
                        "exchange": fs.split(":")[0],
                        "type": "alias",
                    }
                ]
            }
        )

    params = {
        "text": q,
        "hl": "1",
        "lang": "en",
        "search_type": "undefined",
        "domain": "production",
    }
    try:
        resp = http.get(
            TV_SYMBOL_SEARCH_URL,
            params=params,
            headers=TV_SYMBOL_SEARCH_HEADERS,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return jsonify({"error": f"symbol search failed: {e}"}), 502

    symbols = data.get("symbols") if isinstance(data, dict) else None
    if not isinstance(symbols, list):
        symbols = []

    results: list = []
    seen: set[str] = set()
    for hit in symbols:
        if len(results) >= limit:
            break
        full = _tv_hit_full_symbol(hit)
        if not full or full in seen:
            continue
        seen.add(full)
        desc = _tv_strip_html(str(hit.get("description") or ""))
        results.append(
            {
                "fullSymbol": full,
                "description": desc,
                "exchange": str(hit.get("exchange") or hit.get("source_id") or ""),
                "type": str(hit.get("type") or ""),
            }
        )

    return jsonify({"results": results})


@app.route("/")
def chart_root():
    return _send_project_file("index.html")


@app.route("/<path:path>")
def site(path: str):
    if path.startswith("api/"):
        abort(404)
    return _send_project_file(path)


def main():
    print("Pivot Quarters (Flask) — http://127.0.0.1:8787/")
    print("  GET  /health")
    print("  GET  /api/bars?ticker=AMEX:SPY&tf=3m&from=2024-01-01&to=2025-12-31")
    print("  GET  /api/symbol-search?q=SPY&limit=12")
    print('  POST /api/login  JSON {"cookies": "sessionid=...; ..."}')
    print(f"  Session file: {_pickle_path()}")
    app.run(host="0.0.0.0", port=8787, debug=False, threaded=True)


if __name__ == "__main__":
    main()
