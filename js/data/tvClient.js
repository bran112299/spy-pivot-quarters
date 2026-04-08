import { config } from '../config.js';

/** Prefer header input, then same-origin when the chart is served from the TV server (port 8787). */
export function getTvProxyBaseUrl() {
  const el =
    typeof document !== 'undefined' && document.getElementById('tvProxyUrl');
  const raw = el?.value?.trim();
  if (raw) return raw.replace(/\/$/, '');
  if (typeof window !== 'undefined' && window.location?.port === '8787') {
    return window.location.origin.replace(/\/$/, '');
  }
  return config.tvProxyBaseUrl.replace(/\/$/, '');
}

function toYmd(d) {
  const x = d instanceof Date ? d : new Date(d);
  return x.toISOString().slice(0, 10);
}

/**
 * @param {{ ticker: string, tf: string, from?: Date, to?: Date, signal?: AbortSignal }} opts
 */
export async function fetchTvBars(opts) {
  const from = opts.from || new Date(Date.now() - 90 * 86400000);
  const to = opts.to || new Date();
  const q = new URLSearchParams({
    ticker: opts.ticker,
    tf: opts.tf,
    from: toYmd(from),
    to: toYmd(to),
  });
  const url = `${getTvProxyBaseUrl()}/api/bars?${q}`;
  const r = await fetch(url, { cache: 'no-store', signal: opts.signal });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(data.error || `TV proxy HTTP ${r.status}`);
  }
  const candles = data.candles || [];
  return candles.map((c) => ({
    time: typeof c.time === 'number' ? c.time : Math.floor(new Date(c.time).getTime() / 1000),
    open: c.open,
    high: c.high,
    low: c.low,
    close: c.close,
  }));
}

export async function tvProxyHealthy(signal) {
  try {
    const r = await fetch(`${getTvProxyBaseUrl()}/health`, {
      cache: 'no-store',
      signal,
    });
    const j = await r.json();
    return j && j.ok === true;
  } catch (e) {
    if (e && e.name === 'AbortError') throw e;
    return false;
  }
}
