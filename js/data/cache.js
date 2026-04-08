export function cacheKey(symbol, barTf) {
  return `pq_bars_v2_${symbol}_${barTf}`;
}

export function readCache(key) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const o = JSON.parse(raw);
    if (!o || !Array.isArray(o.bars) || !o.bars.length) return null;
    return o;
  } catch (e) {
    return null;
  }
}

export function writeCache(key, bars) {
  try {
    localStorage.setItem(
      key,
      JSON.stringify({
        v: 2,
        saved: Date.now(),
        bars,
      })
    );
  } catch (e) { /* quota */ }
}
