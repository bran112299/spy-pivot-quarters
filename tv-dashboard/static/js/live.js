import { state, TF_MINS, bandColorMap } from './state.js';
import { bandColor } from './utils.js';
import { chart, candleSeries } from './chart.js';
import { applyBands } from './bands.js';
import { setStatus } from './ui.js';

// ── Candle countdown timer ────────────────────────────────────────
const candleTimerEl = document.getElementById('candle-timer');
let candleTimerInterval = null;

export function startCandleTimer(tf) {
  stopCandleTimer();
  const barSecs = (TF_MINS[tf] ?? 1) * 60;
  function tick() {
    const now  = Math.floor(Date.now() / 1000);
    const secs = barSecs - (now % barSecs);
    const m    = Math.floor(secs / 60);
    const s    = secs % 60;
    candleTimerEl.textContent = `${m}:${String(s).padStart(2, '0')}`;
    candleTimerEl.className   = 'on';
  }
  tick();
  candleTimerInterval = setInterval(tick, 1000);
}

export function stopCandleTimer() {
  if (candleTimerInterval) { clearInterval(candleTimerInterval); candleTimerInterval = null; }
  candleTimerEl.className = '';
}

// ── Live badge ────────────────────────────────────────────────────
export function setLiveBadge(s) {
  const el = document.getElementById('live-badge');
  const lb = document.getElementById('live-label');
  if      (s === 'on')    { el.className = 'on';    lb.textContent = 'LIVE'; }
  else if (s === 'stale') { el.className = 'stale'; lb.textContent = 'RECONNECTING'; }
  else                    { el.className = ''; }
}

function resetStaleTimer() {
  if (state.liveTimer) clearTimeout(state.liveTimer);
  state.liveTimer = setTimeout(() => setLiveBadge('stale'), 35000);
}

// ── Candle merging ────────────────────────────────────────────────
function applyLiveCandle(candle) {
  if (!state.chartData.length) return;
  const last = state.chartData[state.chartData.length - 1];
  if (candle.time === last.time) {
    const u = {
      time:  last.time, open: last.open,
      high:  Math.max(last.high, candle.high),
      low:   Math.min(last.low,  candle.low),
      close: candle.close,
    };
    state.chartData[state.chartData.length - 1] = u;
    candleSeries.update(u);
  } else if (candle.time > last.time) {
    state.chartData.push(candle);
    candleSeries.update(candle);
    chart.timeScale().scrollToRealTime();
    if (state.bandSeries) {
      const color = bandColor(candle.time);
      bandColorMap.set(candle.time, color);
      state.bandSeries.update({ time: candle.time, value: 1, color });
    }
  }
}

// ── SSE stream ────────────────────────────────────────────────────
export function stopLive() {
  if (state.liveES)    { state.liveES.close(); state.liveES = null; }
  if (state.liveTimer) { clearTimeout(state.liveTimer); state.liveTimer = null; }
  document.getElementById('live-badge').className = '';
  stopCandleTimer();
}

export function startLive(ticker, tf) {
  stopLive();

  const initBuf  = [];
  let   initDone = false;
  let   initTimer = null;

  function flushInit() {
    initDone = true;
    if (!initBuf.length || !state.chartData.length) {
      console.log(`[flushInit] skipped — initBuf=${initBuf.length} chartData=${state.chartData.length}`);
      return;
    }
    const lastCached = state.chartData[state.chartData.length - 1];
    const firstBuf   = initBuf[0];
    const lastBuf    = initBuf[initBuf.length - 1];
    console.log(`[flushInit] ${ticker} ${tf} — initBuf ${initBuf.length} bars, ` +
      `chartData last=${new Date(lastCached.time*1000).toISOString()}, ` +
      `buf first=${new Date(firstBuf.time*1000).toISOString()}, ` +
      `buf last=${new Date(lastBuf.time*1000).toISOString()}`);

    const patchMap = new Map(initBuf.map(c => [c.time, c]));
    const merged   = state.chartData.filter(c => !patchMap.has(c.time));
    for (const c of initBuf) merged.push(c);
    merged.sort((a, b) => a.time - b.time);

    const added   = merged.length - state.chartData.length;
    const updated = initBuf.filter(c => patchMap.has(c.time)).length;
    console.log(`[flushInit] merged — +${added} new bars, ~${updated} updated bars, total=${merged.length}`);

    state.chartData = merged;
    applyBands(state.chartData);
    candleSeries.setData(state.chartData);
    setStatus(`${state.chartData.length} bars (live)`, 'fetched');
  }

  state.liveES = new EventSource(`/api/live?ticker=${encodeURIComponent(ticker)}&tf=${tf}`);
  state.liveES.onopen = () => {
    setLiveBadge('on');
    resetStaleTimer();
    if (tf !== '1w' && tf !== '1M') startCandleTimer(tf);
  };
  state.liveES.onerror = () => setLiveBadge('stale');
  state.liveES.onmessage = (e) => {
    resetStaleTimer();
    let c; try { c = JSON.parse(e.data); } catch { return; }
    if (!c || typeof c.time !== 'number') return;
    if (!initDone) {
      initBuf.push(c);
      clearTimeout(initTimer);
      if (initBuf.length >= 20) flushInit();
      else initTimer = setTimeout(flushInit, 1500);
      return;
    }
    applyLiveCandle(c);
  };
}
