/**
 * US session tint (EST): premarket yellow, aftermarket blue — same windows as tv-dashboard.
 * Premarket 04:00–09:30 ET, regular clear, aftermarket 16:00–20:00 ET.
 */

export const PRE_COLOR = 'rgba(255, 200, 60, 0.38)';
export const AFT_COLOR = 'rgba(70, 130, 255, 0.34)';
export const NO_COLOR = 'rgba(0,0,0,0)';

/** Minutes since midnight in America/New_York (reliable across browsers). */
export function estMins(ts) {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    hour: 'numeric',
    minute: 'numeric',
    hour12: false,
  }).formatToParts(new Date(ts * 1000));
  const h = parseInt(parts.find((p) => p.type === 'hour')?.value ?? '0', 10);
  const m = parseInt(parts.find((p) => p.type === 'minute')?.value ?? '0', 10);
  return h * 60 + m;
}

export function bandColor(ts) {
  const m = estMins(ts);
  if (m >= 240 && m < 570) return PRE_COLOR;
  if (m >= 960 && m < 1200) return AFT_COLOR;
  return NO_COLOR;
}

export function isIntradayBarTf(barTf) {
  return barTf !== '1d';
}

/**
 * True 24h / overnight product: weekday bars mostly outside regular+extended equity window.
 * Uses strict overnight only (before 4am or after 8pm ET), not 8:00pm exactly — avoids killing
 * SPY extended-hours bars that end at 20:00 ET.
 */
export function detect24hr(candles) {
  let checked = 0;
  let outside = 0;
  for (let i = candles.length - 1; i >= 0 && checked < 300; i--) {
    const ts = candles[i].time;
    const dow = new Date(ts * 1000).getDay();
    if (dow === 0 || dow === 6) continue;
    checked++;
    const m = estMins(ts);
    if (m < 240 || m > 1200) outside++;
  }
  if (checked < 8) return false;
  return outside / checked > 0.85;
}

export function sessionBandsUserEnabled() {
  if (typeof document === 'undefined') return true;
  return document.getElementById('showSessionBands')?.checked !== false;
}

/** @param {object} st chart state with bandSeries */
export function applySessionBands(st, bars, barTf) {
  if (!st.bandSeries || !bars.length) return;

  if (!sessionBandsUserEnabled()) {
    st.bandSeries.setData(
      bars.map((b) => ({ time: b.time, value: 1, color: NO_COLOR }))
    );
    return;
  }

  if (!isIntradayBarTf(barTf) || detect24hr(bars)) {
    st.bandSeries.setData(
      bars.map((b) => ({ time: b.time, value: 1, color: NO_COLOR }))
    );
    return;
  }

  st.bandSeries.setData(
    bars.map((b) => ({
      time: b.time,
      value: 1,
      color: bandColor(b.time),
    }))
  );
}
