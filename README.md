# Pivot Quarters (modular)

Interactive pivot / quarter bands on **lower-timeframe candles** with **higher-timeframe pivot buckets** (default **15m bars**, **8h pivot**, UTC). Data is **TradingView only** via the local server (session cookie).

## Run the chart

```bash
cd "/path/to/untitled folder 2"
pip install -r requirements-proxy.txt   # first time
python3 server/app.py
# same app: python3 server/pivot_tv_proxy.py   or   ./serve.sh
```

Opens **http://127.0.0.1:8787/** — static UI and `/api/*` share one origin (no CORS). Use a **hard refresh** (Cmd+Shift+R) after JS changes.

- **Theme:** **Theme** button (`localStorage`).
- **Symbol:** TradingView form, e.g. `AMEX:SPY` (short label uses the part after `:`).
- **Bars:** 3m / 15m / 1h / 1D from TradingView.
- **Pivot:** 8h / 4h / 1h / 1D / weekly / monthly — aggregation buckets for classic pivot H/L/C; pinned swings use prior bucket H/L vs current bucket’s bar extremes.

## TradingView session

Uses code from [`tv-dashboard`](./tv-dashboard). Session file: `tv-dashboard/cache/cookies.pkl`.

1. With `./serve.sh` running, expand **TradingView cookie** on the chart, paste cookies (must include `sessionid=`), **Save cookie to proxy** — or:

```bash
curl -X POST http://127.0.0.1:8787/api/login \
  -H 'Content-Type: application/json' \
  -d '{"cookies":"sessionid=YOUR_VALUE; ..."}'
```

2. Health: `curl http://127.0.0.1:8787/health` — `cookies: true` when the pickle exists.

3. Optional [`js/config.js`](js/config.js): `tvProxyBaseUrl` default if you serve the UI from somewhere other than port 8787 (otherwise leave the proxy URL field empty and same-origin is used when on 8787).

## Layout

| Path | Role |
|------|------|
| [`index.html`](index.html) | Shell + controls |
| [`css/theme.css`](css/theme.css) | Dark/light variables |
| [`js/app.js`](js/app.js) | Boot, data load, wiring |
| [`js/config.js`](js/config.js) | Defaults, TV bar-TF history windows |
| [`js/data/loadBars.js`](js/data/loadBars.js) | TradingView load + cache |
| [`js/data/tvClient.js`](js/data/tvClient.js) | `/api/bars`, `/health` client |
| [`js/pivot/`](js/pivot/) | Math + period keys |
| [`js/chart/`](js/chart/) | Lightweight Charts bootstrap, draw, crosshair |
| [`server/app.py`](server/app.py) | Flask app: static UI + `/api/bars`, `/api/login`, `/health` |
| [`server/pivot_tv_proxy.py`](server/pivot_tv_proxy.py) | Thin launcher (imports `app`) |
| [`lightweight-charts.standalone.production.js`](lightweight-charts.standalone.production.js) | Local chart lib |

## Notes

- Intraday history window per TF is `TV_BAR_TF_META` in [`js/config.js`](js/config.js) (`rangeDays`); the proxy turns that into a bar count (capped).
- Pivot buckets for `8h` / `4h` / `1h` are **UTC** epoch alignment, not exchange sessions.
