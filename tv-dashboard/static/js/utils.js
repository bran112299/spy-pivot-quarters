import { state, TF_MINS } from './state.js';

export function getTicker() { return document.getElementById('ticker-input').value.trim().toUpperCase(); }
export function getFrom()   { return document.getElementById('date-from').value; }
export function getTo()     { return document.getElementById('date-to').value; }

// ── Intl formatters ───────────────────────────────────────────────
const _nyFmt = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  hour: 'numeric', minute: '2-digit', hour12: true,
  month: 'short', day: 'numeric', year: 'numeric',
});
const _nyTimeFmt = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  hour: 'numeric', minute: '2-digit', hour12: true,
});
const _nyDateFmt = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York',
  month: 'short', day: 'numeric',
});
const _nyMonthOnlyFmt = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York', month: 'short',
});
const _nyMonthYearFmt = new Intl.DateTimeFormat('en-US', {
  timeZone: 'America/New_York', month: 'short', year: '2-digit',
});

export function estMins(ts) {
  const s = new Date(ts * 1000).toLocaleString('en-US', {
    timeZone: 'America/New_York', hour: 'numeric', minute: '2-digit', hour12: false,
  });
  const [h, m] = s.split(':').map(Number);
  return h * 60 + m;
}

function fmtMonthYear(d) {
  const parts = _nyMonthYearFmt.formatToParts(d);
  const month = parts.find(p => p.type === 'month')?.value ?? '';
  const year  = parts.find(p => p.type === 'year')?.value ?? '';
  return `${month} '${year}`;
}

export function fmtTick(ts) {
  const d = new Date(ts * 1000);
  if (state.activeTf === '1M') {
    return d.getUTCMonth() === 0 ? fmtMonthYear(d) : _nyMonthOnlyFmt.format(d);
  }
  if (state.activeTf === '1w') return fmtMonthYear(d);
  if (state.activeTf === '1d') return _nyDateFmt.format(d);
  const timeParts = _nyTimeFmt.formatToParts(d);
  const hourPart  = timeParts.find(p => p.type === 'hour');
  const minPart   = timeParts.find(p => p.type === 'minute');
  const dayperiod = timeParts.find(p => p.type === 'dayPeriod');
  const h = parseInt(hourPart?.value ?? '0');
  const m = parseInt(minPart?.value ?? '0');
  if (h === 12 && m === 0 && dayperiod?.value === 'AM') return _nyDateFmt.format(d);
  const ap = (dayperiod?.value ?? 'AM').toLowerCase();
  return m === 0 ? `${h}${ap}` : `${h}:${String(m).padStart(2, '0')}${ap}`;
}

export function fmtDateEST(ts) {
  return _nyFmt.format(new Date(ts * 1000)) + ' EST';
}

export function fmt(n) {
  if (n == null) return '—';
  const abs = Math.abs(n);
  const dec = abs < 1 ? 6 : abs < 10 ? 4 : 2;
  return Number(n).toLocaleString(undefined, { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

// ── Session band helpers ──────────────────────────────────────────
export const PRE_COLOR = 'rgba(200,160,40,0.10)';
export const AFT_COLOR = 'rgba(50,100,220,0.10)';
export const NO_COLOR  = 'rgba(0,0,0,0)';

export function bandColor(ts) {
  const m = estMins(ts);
  if (m >= 240 && m < 570)  return PRE_COLOR;
  if (m >= 960 && m < 1200) return AFT_COLOR;
  return NO_COLOR;
}

export function isIntraday(tf) { return tf !== '1d'; }

export function detect24hr(candles) {
  let checked = 0;
  for (let i = candles.length - 1; i >= 0 && checked < 200; i--) {
    const ts  = candles[i].time;
    const dow = new Date(ts * 1000).getDay();
    if (dow === 0 || dow === 6) continue;
    checked++;
    const m = estMins(ts);
    if (m < 240 || m >= 1200) return true;
  }
  return false;
}

export function extendBars(bars, periodEnd) {
  if (periodEnd !== Infinity || !bars.length) return bars;
  const barSecs = (TF_MINS[state.activeTf] ?? 1) * 60;
  const last = bars[bars.length - 1];
  return [...bars, ...[1, 2, 3, 4, 5].map(i => last + i * barSecs)];
}
