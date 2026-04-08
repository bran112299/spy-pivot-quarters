# TradingView API Dashboard

A Flask + Lightweight Charts dashboard for streaming and viewing TradingView candle data across any ticker and timeframe.

---

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
# Open http://localhost:5050
```

---

## First-time Login

If `cache/cookies.pkl` does not exist, the browser redirects to `/login`.
Enter your TradingView credentials — the session is saved locally as `cache/cookies.pkl`.
No plaintext credentials are stored. On subsequent runs the cached session loads automatically.

---

## Project Structure

```
tv_viewer/
├── app.py                          # Flask server — routes + session management
├── live_stream.py                  # Shared SSE streamer (WebSocket → SSE fan-out)
├── symbols.py                      # Ticker list helpers
├── example_download.py             # Standalone candle download script
├── requirements.txt
│
├── domain/                         # Core business models
│   ├── candles/                    # Candle + CandlesRepository interfaces
│   ├── trends/                     # Trend + TrendPoint + TrendFactory
│   ├── time_frames.py              # TimeFrame enum
│   └── trading_view/               # TV-specific repository interfaces
│
├── infrastructure/
│   ├── tradingview/
│   │   ├── authentication/         # TradingViewAuthentifier + Session (pickle)
│   │   ├── data/                   # TradingViewDataClient (WebSocket fetch)
│   │   ├── drawing/                # Drawing API client + JWT + ID generator
│   │   ├── time_frames/            # TF enum ↔ TV string converter
│   │   └── trends/                 # Trend serialization
│   └── persistence/                # JSON + CSV candle repositories
│
├── cache/
│   ├── cookies.pkl                 # Session token (gitignored)
│   └── tickers/                    # Per-ticker OHLCV JSON cache files
│
└── static/
    ├── index.html                  # App shell (HTML only)
    ├── login.html                  # Login page
    ├── css/
    │   └── main.css                # All styles
    └── js/                         # ES module frontend
        ├── app.js                  # Entry point — event wiring + init + data loading
        ├── state.js                # Shared mutable state + TF_MINS + cacheKey
        ├── utils.js                # Time formatters, DOM readers, band helpers
        ├── chart.js                # LightweightCharts instance + candleSeries
        ├── bands.js                # Session pre/post-market band rendering
        ├── tooltip.js              # Crosshair OHLC tooltip
        ├── live.js                 # SSE live stream + candle countdown timer
        └── ui.js                   # Overlay, status chip, renderCandles
```

---

## How It Works

### 1. Authentication
`TradingViewAuthentifier` logs into TradingView via its internal API and serializes the session to `cache/cookies.pkl`. Subsequent requests load the pickle directly — no re-login needed.

### 2. Historical Candles
`GET /api/candles?ticker=AMEX:SPY&tf=1d&from=2022-01-01&to=2024-12-31`

- Checks `cache/tickers/` for a matching JSON file first (cache hit → instant response).
- On a miss, opens a TradingView WebSocket via `TradingViewDataClient`, fetches the required bar count, filters to the requested date range, writes JSON to disk, and returns the result.
- `DELETE /api/invalidate` removes the cache file so the next fetch re-downloads from TV.

### 3. Live Streaming
`GET /api/live?ticker=AMEX:SPY&tf=1d`

- Returns a **Server-Sent Events** stream.
- `live_stream.py` maintains a single shared TradingView WebSocket per ticker+tf. Multiple browser tabs subscribe to the same underlying connection via `streamer.subscribe()` / `streamer.unsubscribe()`.
- The frontend accumulates the initial burst of bars from the stream (gap-bridging), merges them with cached history, then applies live tick-by-tick updates.

### 4. Frontend (ES Modules — What is ES?)

**ES** = **ECMAScript** — the official standard that JavaScript is built on. "ES modules" is the native module system built into modern browsers.

Before ES modules, there was no built-in way for one JS file to import code from another. People hacked around it by loading dozens of `<script>` tags in the right order, or using bundlers (Webpack, etc.).

ES modules let you do this natively in the browser:

```js
// state.js
export const state = { activeTf: '8h' };

// app.js
import { state } from './state.js';
```

The browser handles the dependency graph itself — no bundler needed. You opt in with one attribute in your HTML:

```html
<script type="module" src="js/app.js"></script>
```

The browser sees `type="module"`, then follows all the `import` chains automatically.

**Why it matters here:** The old `index.html` had 900+ lines of JS in one `<script>` block. Now each concern lives in its own file and declares exactly what it depends on via `import`. Same behavior, much easier to navigate and modify.

---
The UI is split into focused JS modules loaded via `<script type="module" src="js/app.js">`:

| Module | Responsibility |
|---|---|
| `state.js` | Single source of truth for all mutable state (chartData, activeTf, indicator flags, etc.) |
| `utils.js` | EST time formatters, price formatter, band color logic, `detect24hr` |
| `chart.js` | Creates the LightweightCharts instance and `candleSeries` |
| `bands.js` | Renders pre/post-market histogram bands (4am–9:30am, 4pm–8pm EST) |
| `tooltip.js` | Crosshair OHLC tooltip positioned to stay within chart bounds |
| `live.js` | SSE connection, init-burst flush, candle merging, countdown timer |
| `ui.js` | Overlay spinner, status chip, `renderCandles`, TF dot markers |
| `app.js` | Event listeners, `loadCandles`, `doFetch`, grid/session toggles, init |

---

### 6. Caching Strategy
- **Disk cache** — OHLCV JSON per `ticker|tf|from|to` in `cache/tickers/`. Survives restarts.
- **Memory cache** — `memCache` in `state.js` keyed the same way. Avoids re-parsing disk on TF switches within a session.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serves `index.html` (redirects to `/login` if no session) |
| `GET` | `/login` | Serves `login.html` |
| `POST` | `/api/login` | Authenticates with TradingView, saves session pickle |
| `GET` | `/api/candles` | Returns OHLCV JSON; params: `ticker`, `tf`, `from`, `to` |
| `DELETE` | `/api/invalidate` | Removes disk cache for a given `ticker`/`tf`/`from`/`to` |
| `GET` | `/api/live` | SSE stream of live candles; params: `ticker`, `tf` |

---

## Supported Timeframes

`1m` `3m` `15m` `1h` `4h` `8h` `1D` `1W` `1M`

---

## Example Download Script

Programmatically authenticate and download candles to `cache/tickers/`:

```bash
python example_download.py
```
