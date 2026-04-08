import { state, memCache, cacheKey } from './state.js';
import { getTicker, getFrom, getTo, fmtTick } from './utils.js';
import { chart, candleSeries } from './chart.js';
import { applyBands } from './bands.js';

const overlayEl  = document.getElementById('overlay');
const overlayMsg = document.getElementById('overlay-msg');
const statusChip = document.getElementById('status-chip');
const tooltip    = document.getElementById('tooltip');

export function setOverlay(msg) {
  overlayMsg.textContent = msg || '';
  overlayEl.classList.toggle('hidden', !msg);
}

export function setStatus(text, cls) {
  statusChip.textContent = text;
  statusChip.className   = cls || '';
}

export function updateTfDots() {
  const ticker = getTicker(), from = getFrom(), to = getTo();
  document.querySelectorAll('.tf-btn').forEach(btn => {
    btn.classList.toggle('has-data', !!memCache[cacheKey(ticker, btn.dataset.tf, from, to)]);
  });
}

export function renderCandles(data, statusText, statusCls) {
  state.chartData = [...data].sort((a, b) => a.time - b.time);
  applyBands(state.chartData);
  candleSeries.setData(state.chartData);
  chart.timeScale().applyOptions({
    tickMarkFormatter: fmtTick,
    barSpacing: state.activeTf === '1M' ? 18 : state.activeTf === '1w' ? 6 : undefined,
  });
  chart.timeScale().fitContent();
  setOverlay(null);
  setStatus(statusText, statusCls);
  document.title = `${getTicker()} ${state.activeTf.toUpperCase()}`;
  tooltip.style.display = 'none';
}
