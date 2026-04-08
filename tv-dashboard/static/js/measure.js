import { chart, chartEl } from './chart.js';
import { state } from './state.js';
import { planetSym } from './planetSymbols.js';

let overlay = null;
let measureIdSeq = 0;

function colorForIndex(i) {
  const h = (i * 47) % 360;
  return `hsl(${h}, 65%, 52%)`;
}

function ensureOverlay() {
  if (overlay) return overlay;
  overlay = document.createElement('div');
  overlay.id = 'measure-overlay';
  overlay.className = 'measure-overlay';
  chartEl.parentElement.appendChild(overlay);
  return overlay;
}

function setHint(text) {
  const el = document.getElementById('measure-hint');
  if (!el) return;
  el.textContent = text || '';
}

/** Older /api/ephem/span payloads omitted d_helio; refetch when helio view needs it. */
function needsHelioSpanRefresh(j) {
  if (!j || j.error || !j.per_planet) return false;
  return Object.values(j.per_planet).some(d => d && !Object.prototype.hasOwnProperty.call(d, 'd_helio'));
}

function fetchSpanJson(ts0, ts1, planets) {
  const url = `/api/ephem/span?ts0=${ts0}&ts1=${ts1}&planets=${encodeURIComponent(planets.join(','))}`;
  return fetch(url).then(r => r.json());
}

/** Cumulative °, unsigned remainder as % of 360°, full rotations (e.g. +1.50×). */
function formatMeasureLon(deg) {
  const D = Number(deg);
  if (!Number.isFinite(D)) return '—';
  const rem = ((D % 360) + 360) % 360;
  const pct = (rem / 360) * 100;
  const turns = D / 360;
  const dStr = (D > 0 ? '+' : '') + D.toFixed(2) + '°';
  const tStr = (turns > 0 ? '+' : '') + turns.toFixed(2) + '×';
  return `${dStr} · ${pct.toFixed(2)}%360 · ${tStr}`;
}

function buildCardHtml(j, ts0, ts1, planets) {
  if (!j) return '<div class="m-load">…</div>';
  if (j.error) return `<div class="m-err">${String(j.error)}</div>`;
  const helio = !!state.planets.helio;
  const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  const a0 = new Date(ts0 * 1000).toISOString().slice(0, 10);
  const a1 = new Date(ts1 * 1000).toISOString().slice(0, 10);
  const parts = [];
  parts.push(`<div class="m-title">${esc(a0)} → ${esc(a1)}</div>`);
  for (const p of planets) {
    const d = j.per_planet?.[p];
    if (!d) continue;
    const sym = planetSym(p);
    const useGeo =
      !helio ||
      p === 'Sun' ||
      d.d_helio == null ||
      d.f_helio_360 == null;
    if (useGeo) {
      parts.push(`<div class="m-row"><b>${sym}</b> ${formatMeasureLon(d.d_geo)}</div>`);
    } else {
      parts.push(`<div class="m-row"><b>${sym}</b> ${formatMeasureLon(d.d_helio)}</div>`);
    }
  }
  const pairLines = [];
  for (const pr of j.pairs || []) {
    if (helio) {
      if (pr.f_rel_helio_360 == null || pr.d_rel_helio == null) continue;
      const sa = planetSym(pr.a);
      const sb = planetSym(pr.b);
      pairLines.push(`<div class="m-row m-pair">${sa}${sb} ${formatMeasureLon(pr.d_rel_helio)}</div>`);
    } else {
      const sa = planetSym(pr.a);
      const sb = planetSym(pr.b);
      pairLines.push(`<div class="m-row m-pair">${sa}${sb} ${formatMeasureLon(pr.d_rel)}</div>`);
    }
  }
  if (pairLines.length) {
    parts.push(`<div class="m-sub">${helio ? 'Pairs (helio) /360' : 'Pairs (geo) /360'}</div>`);
    parts.push(...pairLines);
  }
  return parts.join('');
}

async function finalizeMeasurement(ts0, ts1) {
  const planets = [...state.planets.selected];
  if (!planets.length) {
    setHint('Select planets in panel.');
    return;
  }
  const id = ++measureIdSeq;
  const color = colorForIndex(state.measurements.length);
  state.measurements.push({ id, ts0, ts1, color, data: null, planets: [...planets], collapsed: false });
  renderAllMeasurements();

  try {
    const j = await fetchSpanJson(ts0, ts1, planets);
    const m = state.measurements.find(x => x.id === id);
    if (m) m.data = j;
  } catch {
    const m = state.measurements.find(x => x.id === id);
    if (m) m.data = { error: 'Network error' };
  }
  renderAllMeasurements();
}

function queueStaleHelioSpanRefetches() {
  if (!state.planets.helio) return;
  for (const m of state.measurements) {
    if (!m.data || m.data.error || m.spanRefetching) continue;
    if (!needsHelioSpanRefresh(m.data)) continue;
    m.spanRefetching = true;
    const { ts0, ts1, id } = m;
    const planets = m.planets || [];
    fetchSpanJson(ts0, ts1, planets)
      .then(j => {
        const x = state.measurements.find(x => x.id === id);
        if (x) {
          x.data = j;
          x.spanRefetching = false;
        }
        renderAllMeasurements();
      })
      .catch(() => {
        const x = state.measurements.find(x => x.id === id);
        if (x) x.spanRefetching = false;
        renderAllMeasurements();
      });
  }
}

function drawDraftLine() {
  if (!state.measure.on || state.measure.draftTs0 == null) return;
  const x = chart.timeScale().timeToCoordinate(state.measure.draftTs0);
  if (x == null) return;
  const draft = document.createElement('div');
  draft.className = 'measure-draft';
  draft.style.cssText = `position:absolute;left:${x}px;top:0;bottom:0;width:0;border-left:2px dashed rgba(56,139,253,0.65);pointer-events:none;`;
  overlay.appendChild(draft);
}

function drawOneMeasurement(m, index) {
  const y = 16 + index * 46;
  const { ts0, ts1, id, color, data, collapsed } = m;
  const x0 = chart.timeScale().timeToCoordinate(ts0);
  const x1 = chart.timeScale().timeToCoordinate(ts1);
  if (x0 == null || x1 == null) return;

  const left = Math.min(x0, x1);
  const right = Math.max(x0, x1);
  const pad = 12;
  const w = right - left;

  const row = document.createElement('div');
  row.className = 'measure-row';
  row.style.cssText = 'position:absolute;inset:0;pointer-events:none;';

  const vStart = document.createElement('div');
  vStart.className = 'm-vline m-vline-start';
  vStart.style.cssText = `position:absolute;left:${left}px;top:0;bottom:0;width:0;border-left:2px dashed ${color};opacity:0.65;`;
  const vEnd = document.createElement('div');
  vEnd.className = 'm-vline m-vline-end';
  vEnd.style.cssText = `position:absolute;left:${right}px;top:0;bottom:0;width:0;border-left:2px dashed ${color};opacity:0.65;`;

  row.appendChild(vStart);
  row.appendChild(vEnd);

  if (w < pad * 2 + 4) {
    overlay.appendChild(row);
    return;
  }

  const line = document.createElement('div');
  line.className = 'm-line';
  line.style.cssText = `position:absolute;left:${left + pad}px;top:${y}px;width:${w - pad * 2}px;height:2px;background:${color};border-radius:2px;`;

  const aL = document.createElement('div');
  aL.style.cssText = `position:absolute;left:${left}px;top:${y - 5}px;width:0;height:0;border-top:6px solid transparent;border-bottom:6px solid transparent;border-right:10px solid ${color};`;
  const aR = document.createElement('div');
  aR.style.cssText = `position:absolute;left:${right - 10}px;top:${y - 5}px;width:0;height:0;border-top:6px solid transparent;border-bottom:6px solid transparent;border-left:10px solid ${color};`;

  const days = Math.abs(ts1 - ts0) / 86400;
  const daysEl = document.createElement('div');
  daysEl.className = 'm-days';
  daysEl.textContent = `${days.toFixed(days < 3 ? 2 : 1)}d ${collapsed ? '▸' : '▾'}`;
  daysEl.title = collapsed ? 'Show results' : 'Hide results';
  daysEl.addEventListener('click', e => {
    e.preventDefault();
    e.stopPropagation();
    const x = state.measurements.find(x => x.id === id);
    if (!x) return;
    x.collapsed = !x.collapsed;
    renderAllMeasurements();
  });
  daysEl.style.cssText = `position:absolute;left:${left + w / 2 - 22}px;top:${y + 5}px;pointer-events:auto;cursor:pointer;`;

  const card = document.createElement('div');
  card.className = 'measure-card';
  card.style.cssText = [
    'position:absolute',
    `left:${Math.min(Math.max(8, left + w / 2 - 150), chartEl.clientWidth - 308)}px`,
    `top:${y + 26}px`,
    `border-color:${color}`,
    'pointer-events:auto',
  ].join(';');

  const close = document.createElement('button');
  close.type = 'button';
  close.className = 'm-close';
  close.textContent = '×';
  close.title = 'Remove measurement';
  close.addEventListener('click', e => {
    e.stopPropagation();
    e.preventDefault();
    state.measurements = state.measurements.filter(x => x.id !== id);
    renderAllMeasurements();
  });

  const body = document.createElement('div');
  body.className = 'm-card-body';
  body.innerHTML = buildCardHtml(data, ts0, ts1, m.planets || []);

  card.appendChild(close);
  card.appendChild(body);
  row.appendChild(line);
  row.appendChild(aL);
  row.appendChild(aR);
  row.appendChild(daysEl);
  overlay.appendChild(row);
  if (!collapsed) overlay.appendChild(card);
}

export function renderAllMeasurements() {
  ensureOverlay();
  queueStaleHelioSpanRefetches();
  overlay.innerHTML = '';
  drawDraftLine();
  state.measurements.forEach((m, i) => drawOneMeasurement(m, i));
}

export function clearAllMeasurements() {
  state.measurements = [];
  state.measure.draftTs0 = null;
  setHint(state.measure.on ? 'Click start candle…' : '');
  renderAllMeasurements();
}

export function initMeasureTool() {
  chart.timeScale().subscribeVisibleTimeRangeChange(() => renderAllMeasurements());
  new ResizeObserver(() => renderAllMeasurements()).observe(chartEl.parentElement);
}

export function onChartClick(param) {
  if (!state.measure.on) return;
  const ts = param?.time;
  if (typeof ts !== 'number') return;

  if (state.measure.draftTs0 == null) {
    state.measure.draftTs0 = ts;
    setHint('Click end candle…');
    renderAllMeasurements();
    return;
  }

  const ts0 = Math.min(state.measure.draftTs0, ts);
  const ts1 = Math.max(state.measure.draftTs0, ts);
  state.measure.draftTs0 = null;
  setHint('Click start for next measure, or turn Measure off.');
  finalizeMeasurement(ts0, ts1);
}

