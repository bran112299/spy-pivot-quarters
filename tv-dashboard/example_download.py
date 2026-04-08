"""
Example: Download candle data from TradingView for all symbols in symbols.py
for the period Jan 1 2026 to today, then save as JSON.

Usage:
    python example_download.py

Requirements:
    pip install websocket-client backoff requests python-dateutil dataclasses-json
"""

import os
import sys
import json
import pickle
from datetime import datetime

# -- Add project root to path so imports work
sys.path.insert(0, os.path.dirname(__file__))

from domain.time_frames import TimeFrame
from infrastructure.tradingview.authentication.trading_view_authentifier import TradingViewAuthentifier
from infrastructure.tradingview.data.trading_view_data_client import TradingViewDataClient
from infrastructure.tradingview.time_frames.time_frame_converter import TradingViewTimeFrameConverter
import symbols as sym

# ---------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------
COOKIES_PATH = os.path.join("cache", "cookies.pkl")
DATA_DIR = os.path.join("cache", "tickers")
START_DATE = datetime(2026, 1, 1)
# How many daily bars to request — 100 covers Jan 1 2026 to today
BARS_COUNT = 100
TIME_FRAME = TimeFrame.TF_1DAY

# All symbols defined in symbols.py
ALL_SYMBOLS = {
    "SPX": sym.SPX, "ES": sym.ES, "NQ": sym.NQ, "SPY": sym.SPY,
    "GOLD": sym.GOLD, "BTC": sym.BTC, "YM": sym.YM, "DJI": sym.DJI,
    "BITCOIN": sym.BITCOIN, "DIS": sym.DIS, "OIL": sym.OIL, "TSLA": sym.TSLA,
    "AAPL": sym.AAPL, "BA": sym.BA, "SOYBEAN": sym.SOYBEAN,
    "OIL_FUTURES": sym.OIL_FUTURES, "KO": sym.KO, "GBPUSD": sym.GBPUSD,
    "EURUSD": sym.EURUSD, "CATTLE": sym.CATTLE, "RDDT": sym.RDDT,
    "MBT": sym.MBT, "SI": sym.SI,
}
# ---------------------------------------------------------------


def get_session(username: str = None, password: str = None):
    """Load session from cookies.pkl, or login with credentials."""
    auth = TradingViewAuthentifier()

    if os.path.exists(COOKIES_PATH):
        print(f"[auth] Loading session from {COOKIES_PATH}")
        with open(COOKIES_PATH, "rb") as f:
            from infrastructure.tradingview.authentication.trading_view_session import TradingViewSession
            return TradingViewSession.from_dict(pickle.load(f))

    if not username or not password:
        raise RuntimeError(
            "No cookies.pkl found. Provide username and password to login."
        )
    print("[auth] Logging in with credentials...")
    return auth.login(username=username, password=password)


def download_candles(session, ticker_name: str, tv_symbol: str):
    """Download daily candles for a single ticker, filter to START_DATE."""
    converter = TradingViewTimeFrameConverter()
    client = TradingViewDataClient(
        trading_view_time_frame_converter=converter,
        verbose=True
    )

    print(f"  Fetching {ticker_name} ({tv_symbol}) ...")
    candles = client.get_data(
        trading_view_session=session,
        ticker=tv_symbol,
        time_frame=TIME_FRAME,
        bars_count=BARS_COUNT,
    )

    # Filter to START_DATE onward
    filtered = [c for c in candles if c.open_time >= START_DATE]
    return filtered


def candles_to_dict(candles):
    """Convert candle list to JSON-serialisable list of dicts."""
    result = []
    for c in candles:
        result.append({
            "time": c.open_time.isoformat(),
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume,
        })
    return result


def main():
    os.makedirs(DATA_DIR, exist_ok=True)

    # --- Authenticate ---
    # If cookies.pkl exists, no credentials needed.
    # Otherwise set your TV username/password here:
    session = get_session(
        username="your_username_here",
        password="your_password_here",
    )

    all_data = {}
    for name, tv_symbol in ALL_SYMBOLS.items():
        try:
            candles = download_candles(session, name, tv_symbol)
            data = candles_to_dict(candles)
            all_data[name] = {"symbol": tv_symbol, "candles": data}

            # Save individual ticker JSON
            out_path = os.path.join(DATA_DIR, f"{name}.json")
            with open(out_path, "w") as f:
                json.dump(data, f)
            print(f"  -> Saved {len(data)} candles to {out_path}")

        except Exception as e:
            print(f"  [ERROR] {name}: {e}")

    # Save combined file
    combined_path = os.path.join(DATA_DIR, "all_tickers.json")
    with open(combined_path, "w") as f:
        json.dump(all_data, f)
    print(f"\nAll data saved to {combined_path}")


if __name__ == "__main__":
    main()
