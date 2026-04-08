/**
 * @param {number} ts Unix seconds
 * @param {string} mode monthly | weekly | daily | eight_hour | four_hour | one_hour
 */
export function getPivotKey(ts, mode) {
  const d = new Date(ts * 1000);
  if (mode === 'monthly') {
    return `${d.getUTCFullYear()}-${String(d.getUTCMonth() + 1).padStart(2, '0')}`;
  }
  if (mode === 'weekly') {
    const day = d.getUTCDay() || 7;
    const mon = new Date(d);
    mon.setUTCDate(d.getUTCDate() - day + 1);
    return mon.toISOString().slice(0, 10);
  }
  if (mode === 'daily') {
    return d.toISOString().slice(0, 10);
  }
  if (mode === 'eight_hour') {
    const eight = 8 * 3600;
    return String(Math.floor(ts / eight) * eight);
  }
  if (mode === 'four_hour') {
    const four = 4 * 3600;
    return String(Math.floor(ts / four) * four);
  }
  if (mode === 'one_hour') {
    const one = 3600;
    return String(Math.floor(ts / one) * one);
  }
  return String(ts);
}

export function groupPeriods(bars, mode) {
  const map = {};
  const order = [];
  for (let i = 0; i < bars.length; i++) {
    const b = bars[i];
    const k = getPivotKey(b.time, mode);
    if (!map[k]) {
      map[k] = {
        key: k,
        firstTime: b.time,
        high: b.high,
        low: b.low,
        close: b.close,
        bars: [],
      };
      order.push(k);
    }
    const p = map[k];
    if (b.high > p.high) p.high = b.high;
    if (b.low < p.low) p.low = b.low;
    p.close = b.close;
    p.bars.push(b);
  }
  return order.map((k) => map[k]);
}
