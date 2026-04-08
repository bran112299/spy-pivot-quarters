import { state, memCache, cacheKey } from './state.js';
import { getTicker, getFrom, getTo } from './utils.js';
import { chart, candleSeries, applyChartTheme, applyCandleTheme, applyCrosshairForMeasure } from './chart.js';
import { applyBands, clearBands } from './bands.js';
import { setupTooltip } from './tooltip.js';
import { initPlanetUI, togglePlanetPanel, toggleMeasure, clearAllMeasures } from './planets.js';
import { initMeasureTool, onChartClick } from './measure.js';
import { startLive, stopLive } from './live.js';
import { setOverlay, setStatus, updateTfDots, renderCandles } from './ui.js';
import { initTickerSearch, resolveBareTicker } from './tickerSearch.js';

// ── Init ──────────────────────────────────────────────────────────
document.getElementById('date-to').value = new Date().toISOString().slice(0, 10);
setupTooltip();
initTickerSearch();
initPlanetUI();
initMeasureTool();

// Expose onclick handlers (HTML uses onclick="...")
window.doFetch            = doFetch;
window.toggleSessionBands = toggleSessionBands;
window.toggleGrid         = toggleGrid;
window.toggleTheme         = toggleTheme;
window.togglePlanetPanel  = togglePlanetPanel;
window.toggleMeasure      = toggleMeasure;
window.clearAllMeasures   = clearAllMeasures;

// Measure tool needs chart click events
chart.subscribeClick(onChartClick);

// ── Theme toggle ─────────────────────────────────────────────────
function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  applyChartTheme(theme);
  applyCandleTheme(theme);
  applyCrosshairForMeasure(!!state.measure.on);
  // Re-apply grid visibility since applyChartTheme resets grid colors
  chart.applyOptions({ grid: { vertLines: { visible: state.gridOn }, horzLines: { visible: state.gridOn } } });
  localStorage.setItem('theme', theme);
  document.getElementById('theme-toggle').textContent = theme === 'dark' ? '☀' : '⏾';
}

function toggleTheme() {
  applyTheme((document.documentElement.dataset.theme || 'dark') === 'dark' ? 'light' : 'dark');
}

// ── Grid & session toggles ────────────────────────────────────────
function toggleGrid() {
  state.gridOn = !state.gridOn;
  document.getElementById('grid-toggle').classList.toggle('active', state.gridOn);
  chart.applyOptions({
    grid: { vertLines: { visible: state.gridOn }, horzLines: { visible: state.gridOn } },
  });
}

function toggleSessionBands() {
  state.sessionBandsOn = !state.sessionBandsOn;
  document.getElementById('session-toggle').classList.toggle('active', state.sessionBandsOn);
  if (!state.sessionBandsOn) clearBands();
  else applyBands(state.chartData);
}

// ── Data fetching ─────────────────────────────────────────────────
async function doFetch() {
  let ticker = getTicker();
  if (!ticker) return;
  if (!ticker.includes(':')) {
    const resolved = await resolveBareTicker();
    if (!resolved) return;
    ticker = getTicker();
  }
  const from = getFrom(), to = getTo();
  delete memCache[cacheKey(ticker, state.activeTf, from, to)];
  await fetch(`/api/invalidate?ticker=${encodeURIComponent(ticker)}&tf=${state.activeTf}&from=${from}&to=${to}`, { method: 'DELETE' });
  await loadCandles(ticker, state.activeTf, from, to);
}

async function loadCandles(ticker, tf, from, to) {
  const key = cacheKey(ticker, tf, from, to);
  if (memCache[key]) {
    renderCandles(memCache[key], `${memCache[key].length} bars (cached)`, 'cached');
    stopLive(); startLive(ticker, tf);
    return;
  }
  const btn = document.getElementById('fetch-btn');
  btn.disabled = true; btn.textContent = '…';
  setOverlay(`Fetching ${ticker} ${tf.toUpperCase()}…`);
  setStatus('loading…');
  stopLive();
  try {
    const res  = await fetch(`/api/candles?ticker=${encodeURIComponent(ticker)}&tf=${tf}&from=${from}&to=${to}`);
    const json = await res.json();
    if (json.error) { setOverlay('Error: ' + json.error); setStatus('error', 'err'); return; }
    memCache[key] = json.candles;
    updateTfDots();
    renderCandles(
      json.candles,
      `${json.candles.length} bars (${json.cached ? 'cached' : 'fetched'})`,
      json.cached ? 'cached' : 'fetched'
    );
    startLive(ticker, tf);
  } catch {
    setOverlay('Network error'); setStatus('error', 'err');
  } finally {
    btn.disabled = false; btn.textContent = 'Fetch';
  }
}

// ── Settle ────────────────────────────────────────────────────────
function scheduleSettle(ticker, tf) {
  if (state.settleTimer) clearTimeout(state.settleTimer);
  state.settleTimer = setTimeout(() => {
    state.settleTimer = null;
    if (getTicker() !== ticker || state.activeTf !== tf) return;
    silentFixRecentBars(ticker, tf);
  }, 15000);
}

async function silentFixRecentBars(ticker, tf) {
  if (state.chartData.length < 2) return;
  console.log(`[settle] ${ticker} ${tf} — silently fixing last 2 bars after 15s`);
  for (const c of state.chartData.slice(-2)) {
    console.log(`[settle] pushing bar time=${new Date(c.time*1000).toISOString()} close=${c.close}`);
    candleSeries.update(c);
  }
  memCache[cacheKey(ticker, tf, getFrom(), getTo())] = state.chartData;
  console.log(`[settle] done, memCache updated`);
}

// ── Event listeners ───────────────────────────────────────────────
document.querySelectorAll('.tf-btn').forEach(btn => {
  btn.addEventListener('click', async () => {
    const tf = btn.dataset.tf;
    document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    state.activeTf = tf;
    const ticker = getTicker(), from = getFrom(), to = getTo();
    const key = cacheKey(ticker, tf, from, to);
    if (memCache[key]) {
      renderCandles(memCache[key], `${memCache[key].length} bars (cached)`, 'cached');
      stopLive(); startLive(ticker, tf);
    } else {
      await loadCandles(ticker, tf, from, to);
    }
    scheduleSettle(ticker, tf);
  });
});

document.getElementById('date-from').addEventListener('change', updateTfDots);
document.getElementById('date-to').addEventListener('change', updateTfDots);
document.getElementById('ticker-input').addEventListener('change', () => {
  stopLive(); updateTfDots();
});
document.getElementById('ticker-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') doFetch();
});

// ── Apply defaults & initial load ─────────────────────────────────
const savedTheme = localStorage.getItem('theme') || 'dark';
if (savedTheme !== 'dark') applyTheme(savedTheme);
else document.getElementById('theme-toggle').textContent = '☀';

document.getElementById('session-toggle').classList.remove('active');
document.getElementById('grid-toggle').classList.remove('active');
chart.applyOptions({ grid: { vertLines: { visible: false }, horzLines: { visible: false } } });
applyCrosshairForMeasure(!!state.measure.on);

loadCandles(getTicker(), state.activeTf, getFrom(), getTo()).then(() => {
  // initial load complete
});
