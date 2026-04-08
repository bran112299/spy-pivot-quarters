"""
TradingView live candle streamer — single stream at a time.
"""

import json
import re
import string
import random
import threading
import time
import traceback
from typing import Callable, Dict, List, Optional

from websocket._core import create_connection
from infrastructure.tradingview.authentication.trading_view_session import TradingViewSession


def _rand_str(n=12):
    return "".join(random.choices(string.ascii_lowercase, k=n))

def _prepend(st):
    return f"~m~{len(st)}~m~{st}"

def _msg(func, params):
    return _prepend(json.dumps({"m": func, "p": params}, separators=(",", ":")))


# Pre-compiled regex — used on every recv(), worth caching
_RE_HB      = re.compile(r'~h~(\d+)')
_RE_FRAMES  = re.compile(r'~m~\d+~m~')
_RE_SERIES  = re.compile(r'"s":\[(.+?)}]')
_RE_PARTS   = re.compile(r'[:,\[\]]')


def _extract_candles(raw: str) -> List[dict]:
    results = []
    for frame in _RE_FRAMES.split(raw):
        if '"s":[' not in frame:
            continue
        out = _RE_SERIES.search(frame)
        if not out:
            continue
        for raw_candle in out.group(1).split(',{"'):
            parts = _RE_PARTS.split(raw_candle)
            try:
                ts    = abs(float(parts[4]))
                open_ = float(parts[5])
                high  = float(parts[6])
                low   = float(parts[7])
                close = float(parts[8])
                results.append({
                    "time":  int(ts),
                    "open":  round(open_, 6),
                    "high":  round(high,  6),
                    "low":   round(low,   6),
                    "close": round(close, 6),
                })
            except (IndexError, ValueError):
                continue
    return results


class _Stream:
    RECONNECT_DELAY = 5

    def __init__(self, session: TradingViewSession, ticker: str, tv_tf: str):
        self.session  = session
        self.ticker   = ticker
        self.tv_tf    = tv_tf
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, Callable] = {}
        self._cb_lock = threading.Lock()

    def add_callback(self, cb: Callable) -> str:
        sid = _rand_str(8)
        with self._cb_lock:
            self._callbacks[sid] = cb
        return sid

    def remove_callback(self, sid: str):
        with self._cb_lock:
            self._callbacks.pop(sid, None)

    def _notify(self, candle: dict):
        with self._cb_lock:
            cbs = list(self._callbacks.values())
        for cb in cbs:
            try:
                cb(candle)
            except Exception:
                pass

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        with self._cb_lock:
            self._callbacks.clear()

    def _run(self):
        while self._running:
            try:
                self._connect_and_stream()
            except Exception:
                if self._running:
                    print(f"[stream {self.ticker}/{self.tv_tf}] error — reconnecting in {self.RECONNECT_DELAY}s")
                    traceback.print_exc()
                    time.sleep(self.RECONNECT_DELAY)

    def _connect_and_stream(self):
        sess_id    = "qs_" + _rand_str()
        chart_sess = "cs_" + _rand_str()
        headers    = json.dumps({"Origin": "https://data.tradingview.com"})

        ws = create_connection(
            "wss://prodata.tradingview.com/socket.io/websocket",
            headers=headers
        )
        print(f"[stream] connected  {self.ticker} {self.tv_tf}")

        def send(func, params):
            ws.send(_msg(func, params))

        try:
            send("set_auth_token",       [self.session.auth_token])
            send("chart_create_session", [chart_sess, ""])
            send("quote_create_session", [sess_id])
            send("quote_set_fields", [
                sess_id, "ch", "chp", "current_session", "description",
                "local_description", "language", "exchange", "fractional",
                "is_tradable", "lp", "lp_time", "minmov", "minmove2",
                "original_name", "pricescale", "pro_name", "short_name",
                "type", "update_mode", "volume", "currency_code", "rchp", "rtc"
            ])
            send("quote_add_symbols",  [sess_id, self.ticker, {"flags": ["force_permission"]}])
            send("quote_fast_symbols", [sess_id, self.ticker])
            send("resolve_symbol", [
                chart_sess, "symbol_1",
                '={"symbol":"%s","adjustment":"splits","session":"extended"}' % self.ticker
            ])
            send("create_series", [chart_sess, "s1", "s1", "symbol_1", self.tv_tf, 20])

            while self._running:
                try:
                    raw = ws.recv()
                except Exception:
                    break

                hb = _RE_HB.search(raw)
                if hb:
                    ws.send(_prepend(f"~h~{hb.group(1)}"))
                    continue

                for c in _extract_candles(raw):
                    self._notify(c)

        finally:
            try:
                ws.close()
            except Exception:
                pass
            print(f"[stream] disconnected {self.ticker} {self.tv_tf}")


class LiveStreamer:
    def __init__(self):
        self._lock   = threading.Lock()
        self._stream: Optional[_Stream] = None
        self._key    = None

    def subscribe(self, session: TradingViewSession, ticker: str, tv_tf: str,
                  callback: Callable) -> str:
        key = f"{ticker.upper()}|{tv_tf}"
        with self._lock:
            if self._stream is not None and self._key != key:
                print(f"[streamer] switching {self._key} -> {key}")
                self._stream.stop()
                self._stream = None
                self._key    = None
            if self._stream is None:
                s = _Stream(session, ticker.upper(), tv_tf)
                s.start()
                self._stream = s
                self._key    = key
            return self._stream.add_callback(callback)

    def unsubscribe(self, sub_id: str):
        with self._lock:
            if self._stream:
                self._stream.remove_callback(sub_id)

    def stop_all(self):
        with self._lock:
            if self._stream:
                self._stream.stop()
                self._stream = None
                self._key    = None


streamer = LiveStreamer()
