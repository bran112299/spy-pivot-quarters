"""
Alpaca Markets historical bar downloader.
Free tier: data back to ~2016 via IEX feed.
Paid tier: SIP feed with fuller history.
"""
import os
import json
import requests
from datetime import datetime, timezone

ALPACA_BARS_URL = "https://data.alpaca.markets/v2/stocks/{symbol}/bars"
CONFIG_PATH = os.path.join("cache", "alpaca_config.json")
CACHE_DIR   = os.path.join("cache", "alpaca")

# App TF key → Alpaca timeframe string
TF_TO_ALPACA = {
    "1m":  "1Min",
    "3m":  "3Min",
    "15m": "15Min",
    "1h":  "1Hour",
    "4h":  "4Hour",
    "8h":  "8Hour",
    "1d":  "1Day",
    "1w":  "1Week",
    "1M":  "1Month",
}


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_config(key: str, secret: str):
    os.makedirs("cache", exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({"key": key, "secret": secret}, f)


def _headers():
    cfg = load_config()
    if not cfg.get("key") or not cfg.get("secret"):
        raise ValueError("Alpaca API keys not configured")
    return {
        "APCA-API-KEY-ID":     cfg["key"],
        "APCA-API-SECRET-KEY": cfg["secret"],
    }


def download_bars(symbol: str, tf_key: str = "1h", start: str = "2015-01-01",
                  end: str = None, feed: str = "iex", on_progress=None):
    """
    Download all historical bars from Alpaca and save to cache.
    Returns list of {time, open, high, low, close, volume} dicts.
    on_progress(bars_so_far, page_num) called after each page.
    """
    alpaca_tf = TF_TO_ALPACA.get(tf_key)
    if not alpaca_tf:
        raise ValueError(f"Unsupported timeframe: {tf_key}")

    if end is None:
        end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    os.makedirs(CACHE_DIR, exist_ok=True)

    bars = []
    page_token = None
    page = 0

    while True:
        params = {
            "timeframe":  alpaca_tf,
            "start":      start,
            "end":        end,
            "limit":      10000,
            "adjustment": "all",
            "feed":       feed,
            "sort":       "asc",
        }
        if page_token:
            params["page_token"] = page_token

        url  = ALPACA_BARS_URL.format(symbol=symbol.upper())
        resp = requests.get(url, headers=_headers(), params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        batch = data.get("bars", [])
        for b in batch:
            t = datetime.fromisoformat(b["t"].replace("Z", "+00:00"))
            bars.append({
                "time":   int(t.timestamp()),
                "open":   round(b["o"], 6),
                "high":   round(b["h"], 6),
                "low":    round(b["l"], 6),
                "close":  round(b["c"], 6),
                "volume": b.get("v", 0),
            })

        page += 1
        if on_progress:
            on_progress(len(bars), page)

        page_token = data.get("next_page_token")
        if not page_token:
            break

    bars.sort(key=lambda x: x["time"])

    # Save to cache
    cache_file = _cache_path(symbol, tf_key)
    with open(cache_file, "w") as f:
        json.dump({
            "symbol":    symbol.upper(),
            "tf":        tf_key,
            "bars":      bars,
            "updated":   datetime.now(timezone.utc).isoformat(),
        }, f)

    return bars


def load_cached_bars(symbol: str, tf_key: str, from_ts: int = None, to_ts: int = None):
    """Load bars from cache, optionally filtered by Unix timestamp range."""
    path = _cache_path(symbol, tf_key)
    if not os.path.exists(path):
        return None
    with open(path) as f:
        data = json.load(f)
    bars = data["bars"]
    if from_ts is not None:
        bars = [b for b in bars if b["time"] >= from_ts]
    if to_ts is not None:
        bars = [b for b in bars if b["time"] <= to_ts]
    return bars


def list_cached():
    """Return metadata for all cached Alpaca datasets."""
    if not os.path.exists(CACHE_DIR):
        return []
    result = []
    for fname in os.listdir(CACHE_DIR):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(CACHE_DIR, fname)
        try:
            with open(path) as f:
                meta = json.load(f)
            bars = meta.get("bars", [])
            result.append({
                "symbol":  meta.get("symbol", "?"),
                "tf":      meta.get("tf", "?"),
                "bars":    len(bars),
                "from":    datetime.utcfromtimestamp(bars[0]["time"]).strftime("%Y-%m-%d") if bars else None,
                "to":      datetime.utcfromtimestamp(bars[-1]["time"]).strftime("%Y-%m-%d") if bars else None,
                "updated": meta.get("updated"),
            })
        except Exception:
            pass
    return result


def _cache_path(symbol: str, tf_key: str) -> str:
    safe = symbol.upper().replace("/", "_")
    return os.path.join(CACHE_DIR, f"{safe}_{tf_key}.json")
