import os
import sys
import json
import pickle
import re
import queue
import math
import requests as http
from datetime import datetime, date
from flask import Flask, request, jsonify, send_from_directory, redirect, Response

sys.path.insert(0, os.path.dirname(__file__))

from domain.time_frames import TimeFrame
from infrastructure.tradingview.authentication.trading_view_session import TradingViewSession
from infrastructure.tradingview.data.trading_view_data_client import TradingViewDataClient
from infrastructure.tradingview.time_frames.time_frame_converter import TradingViewTimeFrameConverter
from live_stream import streamer
from infrastructure.alpaca_client import (
    save_config as alpaca_save_config,
    load_config as alpaca_load_config,
    download_bars as alpaca_download_bars,
    load_cached_bars as alpaca_load_cached,
    list_cached as alpaca_list_cached,
)

app = Flask(__name__, static_folder="static")

COOKIES_PATH = os.path.join("cache", "cookies.pkl")
CACHE_DIR    = os.path.join("cache", "tickers")

TF_MINUTES = {
    "1m": 1, "3m": 3, "15m": 15,
    "1h": 60, "4h": 240, "8h": 480, "1d": 1440,
    "1w": 10080, "1M": 43200,
}
TF_TO_DOMAIN = {
    "1m":  TimeFrame.TF_1MINUTE,  "3m":  TimeFrame.TF_3MINUTE,
    "15m": TimeFrame.TF_15MINUTE, "1h":  TimeFrame.TF_1HOUR,
    "4h":  TimeFrame.TF_4HOUR,    "8h":  TimeFrame.TF_8HOUR,
    "1d":  TimeFrame.TF_1DAY,     "1w":  TimeFrame.TF_1WEEK,
    "1M":  TimeFrame.TF_1MONTH,
}
TF_TO_TV_VALUE = {
    "1m": "1", "3m": "3", "15m": "15",
    "1h": "60", "4h": "240", "8h": "480", "1d": "1D",
    "1w": "1W", "1M": "M",
}

TV_SYMBOL_SEARCH_URL = "https://symbol-search.tradingview.com/symbol_search/v3/"
TV_SYMBOL_SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Origin": "https://www.tradingview.com",
    "Referer": "https://www.tradingview.com/",
}

_symbol_alias_map_cache: dict | None = None


def _get_symbol_alias_map() -> dict:
    """UPPER short name -> full TradingView symbol from symbols.py."""
    global _symbol_alias_map_cache
    if _symbol_alias_map_cache is None:
        import symbols as sm

        m: dict = {}
        for name in dir(sm):
            if not name.isupper() or name.startswith("_"):
                continue
            val = getattr(sm, name, None)
            if isinstance(val, str) and ":" in val:
                m[name.upper()] = val.upper()
        _symbol_alias_map_cache = m
    return _symbol_alias_map_cache


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


_session_cache = None
_safe_ticker_cache: dict = {}

@app.after_request
def add_no_cache_headers(resp):
    # Prevent stale UI after branch switches / rebuilds.
    # (Browsers can be aggressive about caching module scripts + HTML.)
    try:
        p = (request.path or "").lower()
        if p.endswith((".html", ".js", ".css")) or p in ("/", "/login"):
            resp.headers["Cache-Control"] = "no-store, max-age=0"
            resp.headers["Pragma"] = "no-cache"
    except Exception:
        pass
    return resp


def cookies_exist():
    return os.path.exists(COOKIES_PATH)


def load_session():
    global _session_cache
    if _session_cache:
        return _session_cache
    with open(COOKIES_PATH, "rb") as f:
        _session_cache = TradingViewSession.from_dict(pickle.load(f))
    return _session_cache


def save_session(session):
    global _session_cache
    os.makedirs("cache", exist_ok=True)
    with open(COOKIES_PATH, "wb") as f:
        pickle.dump(session.to_dict(), f)
    _session_cache = session


def cache_path(ticker, tf, from_date, to_date):
    t = ticker.upper()
    if t not in _safe_ticker_cache:
        _safe_ticker_cache[t] = re.sub(r"[^\w]", "_", t)
    return os.path.join(CACHE_DIR, f"{_safe_ticker_cache[t]}_{tf}_{from_date}_{to_date}.json")


def _get_candles(ticker, tf_key, bars_count):
    """Shared helper â€” opens one TV websocket and returns candle list."""
    print(f"[candles] fetching {ticker} {tf_key} â€” {bars_count} bars")
    session   = load_session()
    converter = TradingViewTimeFrameConverter()
    client    = TradingViewDataClient(
        trading_view_time_frame_converter=converter, verbose=False)
    result = client.get_data(
        trading_view_session=session,
        ticker=ticker.upper(),
        time_frame=TF_TO_DOMAIN[tf_key],
        bars_count=bars_count,
    )
    print(f"[candles] got {len(result)} candles for {ticker} {tf_key}")
    return result


def fetch_candles(ticker, tf, from_date, to_date):
    tf_key = tf
    mins   = TF_MINUTES[tf_key]
    bars   = max(500, int((to_date - from_date).days * 24 * 60 / mins) + 50)
    print(f"[candles] date range {from_date} -> {to_date}, requesting {bars} bars")

    candles = _get_candles(ticker, tf_key, bars)

    from_dt = datetime(from_date.year, from_date.month, from_date.day)
    to_dt   = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59)

    data = [
        {"time": int(c.open_time.timestamp()),
         "open": round(c.open, 6), "high": round(c.high, 6),
         "low":  round(c.low,  6), "close": round(c.close, 6)}
        for c in candles if from_dt <= c.open_time <= to_dt
    ]
    with open(cache_path(ticker, tf_key, from_date, to_date), "w") as f:
        json.dump(data, f)
    return data


def parse_date(s, fallback):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return fallback


# â”€â”€ Ephemeris (PyEphem) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
try:
    import ephem
except Exception:
    ephem = None

PLANET_ALIASES = {
    "sun": "Sun",
    "moon": "Moon",
    "mercury": "Mercury",
    "venus": "Venus",
    "mars": "Mars",
    "jupiter": "Jupiter",
    "saturn": "Saturn",
    "uranus": "Uranus",
    "neptune": "Neptune",
    "pluto": "Pluto",
}

MAJOR_ASPECTS = [
    ("conj", 0.0),
    ("sext", 60.0),
    ("sq", 90.0),
    ("tri", 120.0),
    ("opp", 180.0),
]


def _norm_deg(x: float) -> float:
    x = float(x) % 360.0
    return x + 360.0 if x < 0 else x


def _signed_shortest_delta_deg(a0: float, a1: float) -> float:
    """Signed shortest delta taking wrap into account: a1-a0 in [-180, +180)."""
    d = (_norm_deg(a1) - _norm_deg(a0) + 180.0) % 360.0 - 180.0
    return d


def _unwrap_delta_deg(a0: float, a1: float) -> float:
    """
    Return delta in degrees that is intuitive for "movement" over a span.
    For planets, shortest signed delta is typically what we want.
    """
    return _signed_shortest_delta_deg(a0, a1)


def _lerp_ephem_date(ed0: "ephem.Date", ed1: "ephem.Date", frac: float) -> "ephem.Date":
    frac = max(0.0, min(1.0, float(frac)))
    t0 = float(ephem.Date(ed0))
    t1 = float(ephem.Date(ed1))
    return ephem.Date(t0 + frac * (t1 - t0))


def _span_sample_steps_from_dates(ed0: "ephem.Date", ed1: "ephem.Date") -> int:
    """Number of subintervals for cumulative longitude along [ed0, ed1]."""
    days = abs(float(ephem.Date(ed1)) - float(ephem.Date(ed0)))
    n = max(1, int(days * 4))
    return max(64, min(512, n))


def _init_bodies_for_span(planets: list) -> tuple[dict, object | None]:
    """Body instances for each requested name; optional Sun if not requested."""
    bodies: dict = {}
    for name in planets:
        ctor = getattr(ephem, name, None)
        if ctor is None:
            continue
        bodies[name] = ctor()
    sun_fallback = ephem.Sun() if "Sun" not in bodies else None
    return bodies, sun_fallback


def _snapshot_geo_hel_at(
    bodies: dict, sun_fallback, planets: list, ed: "ephem.Date"
) -> tuple[dict, dict]:
    """Geo/heli longitudes at one time; matches api_ephem/span endpoint conventions."""
    geo: dict = {}
    hel: dict = {}
    for name in planets:
        body = bodies.get(name)
        if body is None:
            continue
        geo[name] = _geo_lon_deg(body, ed)
        if name == "Sun":
            v = _helio_lon_deg(body, ed)
            if v is not None:
                hel["Earth"] = v
        else:
            v = _helio_lon_deg(body, ed)
            if v is not None:
                hel[name] = v
    if "Sun" not in geo:
        s = sun_fallback
        if s is None:
            s = ephem.Sun()
        geo["Sun"] = _geo_lon_deg(s, ed)
        v = _helio_lon_deg(s, ed)
        if v is not None:
            hel["Earth"] = v
    return geo, hel


def _to_ephem_date(ts: int) -> "ephem.Date":
    dt = datetime.utcfromtimestamp(int(ts))
    return ephem.Date(dt)


def _parse_planets_param(raw: str):
    if not raw:
        return ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn"]
    out = []
    for part in raw.split(","):
        key = part.strip()
        if not key:
            continue
        canon = PLANET_ALIASES.get(key.lower(), key)
        if canon in PLANET_ALIASES.values() and canon not in out:
            out.append(canon)
    return out


def _geo_lon_deg(body, edate) -> float:
    body.compute(edate)
    ecl = ephem.Ecliptic(body)
    return _norm_deg(float(ecl.lon) * 180.0 / math.pi)


def _helio_lon_deg(body, edate) -> float | None:
    # Most planets expose .hlon. Sun is special: Sun().hlon returns Earth's heliocentric longitude.
    try:
        body.compute(edate)
        return _norm_deg(float(body.hlon) * 180.0 / math.pi)
    except Exception:
        return None


def _compute_aspects(geo_map: dict, orb_deg: float):
    names = sorted(geo_map.keys())
    aspects = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = names[i]
            b = names[j]
            da = geo_map[a]
            db = geo_map[b]
            sep = abs(_signed_shortest_delta_deg(da, db))  # 0..180
            best = None
            for code, ang in MAJOR_ASPECTS:
                diff = abs(sep - ang)
                if diff <= orb_deg and (best is None or diff < best["orb"]):
                    best = {"a": a, "b": b, "aspect": code, "exact": ang, "sep": sep, "orb": diff}
            if best:
                aspects.append(best)
    aspects.sort(key=lambda x: (x["orb"], x["a"], x["b"]))
    return aspects


# â”€â”€ Routes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route("/")
def index():
    if not cookies_exist():
        return redirect("/login")
    return send_from_directory("static", "index.html")


@app.route("/login")
def login_page():
    return send_from_directory("static", "login.html")


@app.route("/api/login", methods=["POST"])
def api_login():
    body = request.get_json() or {}
    cookies = body.get("cookies", "").strip()
    if not cookies:
        return jsonify({"error": "cookies are required"}), 400
    m = re.search(r'(?:^|;\s*)sessionid=([^;]+)', cookies)
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
            m = re.search(pattern, resp.text)
            if m:
                auth_token = m.group(1)
                break
        if not auth_token:
            return jsonify({"error": "Could not extract auth token â€” cookies may be expired."}), 401
        session = TradingViewSession(session_id=sessionid, auth_token=auth_token, user_id="")
        save_session(session)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    seen: set = set()
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


@app.route("/api/candles")
def api_candles():
    ticker    = request.args.get("ticker", "AMEX:SPY").strip()
    tf        = request.args.get("tf", "1d").strip()
    from_date = parse_date(request.args.get("from", ""), date(2022, 1, 1))
    to_date   = parse_date(request.args.get("to",   ""), date.today())

    path = cache_path(ticker, tf, from_date, to_date)
    if os.path.exists(path):
        with open(path) as f:
            return jsonify({"candles": json.load(f), "cached": True})
    try:
        return jsonify({"candles": fetch_candles(ticker, tf, from_date, to_date), "cached": False})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/ephem")
def api_ephem():
    if ephem is None:
        return jsonify({"error": "PyEphem not installed. `pip install ephem` and restart server."}), 500

    try:
        ts = int(request.args.get("ts", "0"))
        planets = _parse_planets_param(request.args.get("planets", ""))
        orb = float(request.args.get("orb", "1.0"))
    except Exception as e:
        return jsonify({"error": f"bad params: {e}"}), 400

    if ts <= 0:
        return jsonify({"error": "ts is required (unix seconds)"}), 400
    if orb < 0 or orb > 30:
        return jsonify({"error": "orb out of range"}), 400

    edate = _to_ephem_date(ts)

    geo = {}
    helio = {}
    for name in planets:
        body_ctor = getattr(ephem, name, None)
        if body_ctor is None:
            continue
        body = body_ctor()
        geo[name] = _geo_lon_deg(body, edate)
        # Helio:
        if name == "Sun":
            # Special: Sun().hlon == Earth's heliocentric longitude
            helio["Earth"] = _helio_lon_deg(body, edate)
        else:
            helio[name] = _helio_lon_deg(body, edate)

    aspects = _compute_aspects(geo, orb)
    helio_aspect_map = {
        name: helio[name]
        for name in planets
        if name != "Sun" and helio.get(name) is not None
    }
    aspects_helio = _compute_aspects(helio_aspect_map, orb) if len(helio_aspect_map) >= 2 else []

    return jsonify(
        {
            "ts": ts,
            "planets": planets,
            "orb": orb,
            "geo": geo,
            "helio": helio,
            "aspects": aspects,
            "aspects_helio": aspects_helio,
        }
    )


@app.route("/api/ephem/span")
def api_ephem_span():
    if ephem is None:
        return jsonify({"error": "PyEphem not installed. `pip install ephem` and restart server."}), 500

    try:
        ts0 = int(request.args.get("ts0", "0"))
        ts1 = int(request.args.get("ts1", "0"))
        planets = _parse_planets_param(request.args.get("planets", ""))
    except Exception as e:
        return jsonify({"error": f"bad params: {e}"}), 400

    if ts0 <= 0 or ts1 <= 0:
        return jsonify({"error": "ts0 and ts1 are required (unix seconds)"}), 400

    ed0 = _to_ephem_date(ts0)
    ed1 = _to_ephem_date(ts1)

    n_sub = _span_sample_steps_from_dates(ed0, ed1)
    bodies, sun_fallback = _init_bodies_for_span(planets)

    geo_samples: list = []
    hel_samples: list = []
    for k in range(n_sub + 1):
        ed = _lerp_ephem_date(ed0, ed1, k / n_sub)
        g, h = _snapshot_geo_hel_at(bodies, sun_fallback, planets, ed)
        geo_samples.append(g)
        hel_samples.append(h)

    geo0 = geo_samples[0]
    geo1 = geo_samples[-1]
    hel0 = hel_samples[0]
    hel1 = hel_samples[-1]

    def frac360(d):
        return d / 360.0

    per_planet = {}
    for name in planets:
        if name not in geo0 or name not in geo1:
            continue
        d_geo = 0.0
        for k in range(1, len(geo_samples)):
            d_geo += _signed_shortest_delta_deg(geo_samples[k - 1][name], geo_samples[k][name])

        d_helio = None
        if name != "Sun":
            if all(
                hel_samples[k].get(name) is not None for k in range(len(hel_samples))
            ):
                d_helio = 0.0
                for k in range(1, len(hel_samples)):
                    d_helio += _signed_shortest_delta_deg(
                        hel_samples[k - 1][name], hel_samples[k][name]
                    )

        per_planet[name] = {
            "geo0": geo0[name],
            "geo1": geo1[name],
            "d_geo": d_geo,
            "f_geo_360": frac360(d_geo),
            "d_helio": d_helio,
            "f_helio_360": (frac360(d_helio) if d_helio is not None else None),
        }

    pairs = []
    names = [p for p in planets if p in geo0 and p in geo1]
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = names[i]
            b = names[j]
            d_rel = 0.0
            for k in range(1, len(geo_samples)):
                s0 = _norm_deg(geo_samples[k - 1][a] - geo_samples[k - 1][b])
                s1 = _norm_deg(geo_samples[k][a] - geo_samples[k][b])
                d_rel += _signed_shortest_delta_deg(s0, s1)
            row = {"a": a, "b": b, "d_rel": d_rel, "f_rel_360": frac360(d_rel)}

            hel_ok = all(
                hel_samples[k].get(a) is not None
                and hel_samples[k].get(b) is not None
                for k in range(len(hel_samples))
            )
            if hel_ok:
                d_rh = 0.0
                for k in range(1, len(hel_samples)):
                    h0 = _norm_deg(hel_samples[k - 1][a] - hel_samples[k - 1][b])
                    h1 = _norm_deg(hel_samples[k][a] - hel_samples[k][b])
                    d_rh += _signed_shortest_delta_deg(h0, h1)
                row["d_rel_helio"] = d_rh
                row["f_rel_helio_360"] = frac360(d_rh)
            pairs.append(row)

    pairs.sort(key=lambda x: (x["a"], x["b"]))
    return jsonify({"ts0": ts0, "ts1": ts1, "planets": planets, "per_planet": per_planet, "pairs": pairs})


@app.route("/api/invalidate", methods=["DELETE"])
def api_invalidate():
    ticker    = request.args.get("ticker", "AMEX:SPY").strip()
    tf        = request.args.get("tf", "1d").strip()
    from_date = parse_date(request.args.get("from", ""), date(2022, 1, 1))
    to_date   = parse_date(request.args.get("to",   ""), date.today())

    path = cache_path(ticker, tf, from_date, to_date)
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    return jsonify({"ok": True})


@app.route("/api/live")
def api_live():
    ticker = request.args.get("ticker", "AMEX:SPY").strip().upper()
    tf     = request.args.get("tf", "1d").strip()

    if tf not in TF_TO_TV_VALUE:
        return jsonify({"error": "Unsupported tf"}), 400

    tv_value = TF_TO_TV_VALUE[tf]
    session  = load_session()
    q        = queue.Queue(maxsize=200)

    def on_candle(candle):
        try:
            q.put_nowait(candle)
        except queue.Full:
            pass

    sub_id = streamer.subscribe(session, ticker, tv_value, on_candle)
    print(f"[SSE] client connected â€” {ticker} {tf} (sub={sub_id})")

    def generate():
        yield ": connected\n\n"
        try:
            while True:
                try:
                    candle = q.get(timeout=30)
                    yield f"data: {json.dumps(candle)}\n\n"
                except queue.Empty:
                    yield ": ping\n\n"
        except GeneratorExit:
            pass
        finally:
            streamer.unsubscribe(sub_id)
            print(f"[SSE] client disconnected â€” {ticker} {tf} (sub={sub_id})")

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# â”€â”€ Alpaca Routes â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

@app.route("/api/alpaca/keys", methods=["GET"])
def alpaca_get_keys():
    cfg = alpaca_load_config()
    key = cfg.get("key", "")
    return jsonify({
        "configured": bool(key),
        "key_hint":   key[:4] + "â€¦" + key[-4:] if len(key) > 8 else ("set" if key else ""),
    })


@app.route("/api/alpaca/keys", methods=["POST"])
def alpaca_save_keys():
    body   = request.get_json() or {}
    key    = body.get("key", "").strip()
    secret = body.get("secret", "").strip()
    if not key or not secret:
        return jsonify({"error": "key and secret required"}), 400
    alpaca_save_config(key, secret)
    return jsonify({"ok": True})


@app.route("/api/alpaca/download")
def alpaca_download():
    """Stream download progress via SSE."""
    symbol = request.args.get("symbol", "SPY").strip().upper()
    tf     = request.args.get("tf", "1h").strip()
    start  = request.args.get("start", "2015-01-01").strip()
    feed   = request.args.get("feed", "iex").strip()

    def generate():
        yield f"data: {json.dumps({'status': 'starting', 'symbol': symbol, 'tf': tf})}\n\n"
        try:
            def on_progress(total, page):
                yield_val = f"data: {json.dumps({'status': 'progress', 'bars': total, 'page': page})}\n\n"
                # Can't yield from callback â€” use a queue instead (handled below)
                pass

            bars = alpaca_download_bars(symbol, tf, start=start, feed=feed)
            yield f"data: {json.dumps({'status': 'done', 'bars': len(bars)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/alpaca/download", methods=["POST"])
def alpaca_download_post():
    """Blocking download â€” returns when complete."""
    body   = request.get_json() or {}
    symbol = body.get("symbol", "SPY").strip().upper()
    tf     = body.get("tf", "1h").strip()
    start  = body.get("start", "2015-01-01").strip()
    feed   = body.get("feed", "iex").strip()
    try:
        bars = alpaca_download_bars(symbol, tf, start=start, feed=feed)
        return jsonify({"ok": True, "bars": len(bars), "symbol": symbol, "tf": tf})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/alpaca/cached")
def alpaca_cached():
    return jsonify({"datasets": alpaca_list_cached()})


@app.route("/api/alpaca/candles")
def alpaca_candles():
    symbol  = request.args.get("symbol", "SPY").strip().upper()
    tf      = request.args.get("tf", "1h").strip()
    from_ts = int(request.args.get("from_ts", 0)) or None
    to_ts   = int(request.args.get("to_ts", 0)) or None
    bars = alpaca_load_cached(symbol, tf, from_ts, to_ts)
    if bars is None:
        return jsonify({"error": f"No cached Alpaca data for {symbol} {tf}. Download it first."}), 404
    return jsonify({"candles": bars, "source": "alpaca"})


if __name__ == "__main__":
    os.makedirs(CACHE_DIR, exist_ok=True)
    os.makedirs("static", exist_ok=True)
    print("Starting on http://localhost:5050")
    app.run(host="0.0.0.0", port=5050, debug=False, threaded=True)
