/**
 * Intraday pivot buckets:
 * - **Futures** (TV-style session): America/New_York **02:00 / 10:00 / 18:00** for 8h
 *   (matches US index futures on TradingView).
 * - **Everything else**: UTC calendar hours (8h @ 00/08/16 UTC, etc.) so equities are
 *   not forced into the extended-hours futures grid.
 *
 * @param {number} ts Unix seconds
 * @param {string} mode monthly | weekly | daily | eight_hour | four_hour | one_hour
 * @param {string} [symbol] e.g. CME_MINI:ES1! — drives futures vs UTC intraday
 */

const TZ_NY = 'America/New_York';

/** Uppercased TV `EXCHANGE:SYMBOL` exchange ids treated as futures for pivot bucketing. */
const FUTURES_EXCHANGES = new Set([
  'CME',
  'CME_MINI',
  'COMEX',
  'COMEX_MINI',
  'CBOT',
  'CBOT_MINI',
  'NYMEX',
  'NYMEX_MINI',
  'ICEUS',
  'CFE',
  'EUREX',
  'BMFBOVESPA',
  'HKFE',
  'SGX',
  'ASX24',
]);

export function isFuturesSymbol(symbol) {
  if (!symbol || typeof symbol !== 'string') return false;
  const i = symbol.indexOf(':');
  const ex = (i >= 0 ? symbol.slice(0, i) : '').toUpperCase();
  return FUTURES_EXCHANGES.has(ex);
}

function pad2(n) {
  return String(n).padStart(2, '0');
}

/** ET calendar components for instant `ts` (DST-aware via Intl). */
export function etWallParts(ts) {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: TZ_NY,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(new Date(ts * 1000));
  const get = (ty) => parseInt(parts.find((p) => p.type === ty).value, 10);
  return {
    y: get('year'),
    mo: get('month'),
    d: get('day'),
    h: get('hour'),
    mi: get('minute'),
    s: get('second'),
  };
}

function isLeap(y) {
  return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
}

function daysInMonth(y, mo) {
  const dim = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (mo === 2 && isLeap(y)) return 29;
  return dim[mo - 1];
}

/** Previous calendar day in the ET wall calendar (y,mo,d are ET date parts). */
function etCalendarPrevDay(y, mo, d) {
  let dd = d - 1;
  let mm = mo;
  let yy = y;
  if (dd < 1) {
    mm -= 1;
    if (mm < 1) {
      mm = 12;
      yy -= 1;
    }
    dd = daysInMonth(yy, mm);
  }
  return { y: yy, mo: mm, d: dd };
}

function ymd(y, mo, d) {
  return `${y}-${pad2(mo)}-${pad2(d)}`;
}

/**
 * "Session date" for pivots: 02:00 ET starts the ET calendar day for bucketing.
 * Times in [00:00, 02:00) ET still belong to the **previous** session date.
 */
function sessionDateYmd(ts) {
  const { y, mo, d, h } = etWallParts(ts);
  if (h >= 2) return ymd(y, mo, d);
  const p = etCalendarPrevDay(y, mo, d);
  return ymd(p.y, p.mo, p.d);
}

function decimalHourEt(ts) {
  const { h, mi, s } = etWallParts(ts);
  return h + mi / 60 + s / 3600;
}

/** 8h slots aligned to 02:00, 10:00, 18:00 ET (includes 10am boundary). */
function eightHourKeyNy(ts) {
  const { y, mo, d } = etWallParts(ts);
  const dec = decimalHourEt(ts);
  let slot;
  let sdY = y;
  let sdMo = mo;
  let sdD = d;
  if (dec >= 2 && dec < 10) slot = 0;
  else if (dec >= 10 && dec < 18) slot = 1;
  else if (dec >= 18) slot = 2;
  else {
    slot = 2;
    const p = etCalendarPrevDay(y, mo, d);
    sdY = p.y;
    sdMo = p.mo;
    sdD = p.d;
  }
  return `${ymd(sdY, sdMo, sdD)}-8h${slot}`;
}

/** 4h slots from 02:00 ET: 2,6,10,14,18,22. */
function fourHourKeyNy(ts) {
  const dec = decimalHourEt(ts);
  const { y, mo, d } = etWallParts(ts);
  let slot;
  let sdY = y;
  let sdMo = mo;
  let sdD = d;

  if (dec >= 2 && dec < 6) slot = 0;
  else if (dec >= 6 && dec < 10) slot = 1;
  else if (dec >= 10 && dec < 14) slot = 2;
  else if (dec >= 14 && dec < 18) slot = 3;
  else if (dec >= 18 && dec < 22) slot = 4;
  else if (dec >= 22) slot = 5;
  else {
    slot = 5;
    const p = etCalendarPrevDay(y, mo, d);
    sdY = p.y;
    sdMo = p.mo;
    sdD = p.d;
  }
  return `${ymd(sdY, sdMo, sdD)}-4h${slot}`;
}

/** 1h buckets in Eastern time (hour 0–23 on session date). */
function oneHourKeyNy(ts) {
  const { h } = etWallParts(ts);
  return `${sessionDateYmd(ts)}-1h${pad2(h)}`;
}

/** 8h slots 00:00–07:59, 08:00–15:59, 16:00–23:59 UTC. */
function eightHourKeyUtc(ts) {
  const d = new Date(ts * 1000);
  const y = d.getUTCFullYear();
  const mo = d.getUTCMonth() + 1;
  const day = d.getUTCDate();
  const h = d.getUTCHours();
  const slot = Math.floor(h / 8);
  return `${ymd(y, mo, day)}-8h${slot}`;
}

/** 4h slots on the UTC calendar day (0,4,8,12,16,20). */
function fourHourKeyUtc(ts) {
  const d = new Date(ts * 1000);
  const y = d.getUTCFullYear();
  const mo = d.getUTCMonth() + 1;
  const day = d.getUTCDate();
  const h = d.getUTCHours();
  const slot = Math.floor(h / 4);
  return `${ymd(y, mo, day)}-4h${slot}`;
}

/** 1h buckets UTC (calendar UTC date + hour). */
function oneHourKeyUtc(ts) {
  const d = new Date(ts * 1000);
  const y = d.getUTCFullYear();
  const mo = d.getUTCMonth() + 1;
  const day = d.getUTCDate();
  const h = d.getUTCHours();
  return `${ymd(y, mo, day)}-1h${pad2(h)}`;
}

/**
 * @param {number} ts Unix seconds
 * @param {string} mode monthly | weekly | daily | eight_hour | four_hour | one_hour
 * @param {string} [symbol]
 */
export function getPivotKey(ts, mode, symbol = '') {
  const d = new Date(ts * 1000);
  const nyIntraday = isFuturesSymbol(symbol);

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
    const { y, mo, d: dd } = etWallParts(ts);
    return ymd(y, mo, dd);
  }
  if (mode === 'eight_hour') {
    return nyIntraday ? eightHourKeyNy(ts) : eightHourKeyUtc(ts);
  }
  if (mode === 'four_hour') {
    return nyIntraday ? fourHourKeyNy(ts) : fourHourKeyUtc(ts);
  }
  if (mode === 'one_hour') {
    return nyIntraday ? oneHourKeyNy(ts) : oneHourKeyUtc(ts);
  }
  return String(ts);
}

export function groupPeriods(bars, mode, symbol = '') {
  const map = {};
  const order = [];
  for (let i = 0; i < bars.length; i++) {
    const b = bars[i];
    const k = getPivotKey(b.time, mode, symbol);
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
