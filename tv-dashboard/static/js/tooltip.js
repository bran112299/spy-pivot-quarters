import { fmt, fmtDateEST } from './utils.js';
import { chart, candleSeries, chartEl } from './chart.js';
import { state } from './state.js';
import { planetSym } from './planetSymbols.js';

function selectedPlanets() {
  return [...state.planets.selected];
}

function orbDeg() {
  const v = Number(state.planets.orbDeg);
  return Number.isFinite(v) ? Math.max(0, Math.min(10, v)) : 1.0;
}

const tooltip = document.getElementById('tooltip');
const tDate   = document.getElementById('t-date');
const tO      = document.getElementById('t-o');
const tH      = document.getElementById('t-h');
const tL      = document.getElementById('t-l');
const tC      = document.getElementById('t-c');

let planetBox = null;

export function invalidateEphemTooltipCache() {
  lastTs = -1;
  lastEphemJson = null;
}

function ensurePlanetBox() {
  if (planetBox) return planetBox;
  planetBox = document.createElement('div');
  planetBox.id = 't-planets';
  tooltip.appendChild(planetBox);
  return planetBox;
}

function normDeg(x) {
  let v = x % 360;
  if (v < 0) v += 360;
  return v;
}

function formatLon(lon) {
  const z = ['Ar', 'Ta', 'Ge', 'Cn', 'Le', 'Vi', 'Li', 'Sc', 'Sg', 'Cp', 'Aq', 'Pi'];
  const L = normDeg(lon);
  const sign = Math.floor(L / 30);
  const degIn = L - sign * 30;
  const d = Math.floor(degIn);
  const m = Math.floor((degIn - d) * 60);
  return `${String(d).padStart(2, '0')}°${String(m).padStart(2, '0')}' ${z[sign]}`;
}

let lastTs = -1;
let lastReqId = 0;
/** Last successful /api/ephem payload (for instant helio/geo toggle without refetch). */
let lastEphemJson = null;

function renderPlanetBoxLoading(box, orb) {
  box.textContent = '';
  box.className = 'tp-planets';
  const head = document.createElement('div');
  head.className = 'tp-head';
  const frame = state.planets.helio ? 'Helio' : 'Geo';
  head.textContent = `Orb ${orb.toFixed(1)}° · ${frame} · …`;
  box.appendChild(head);
}

function lonForTooltip(p, j) {
  const geo = j.geo || {};
  const helio = j.helio || {};
  if (!state.planets.helio) return geo[p];
  if (p === 'Sun') return geo[p];
  const h = helio[p];
  return h != null ? h : geo[p];
}

function renderPlanetBoxData(box, j, planets, orb) {
  box.textContent = '';
  box.className = 'tp-planets';
  const helioView = !!state.planets.helio;
  const aspects = helioView ? (j.aspects_helio || []) : (j.aspects || []);

  const head = document.createElement('div');
  head.className = 'tp-head';
  head.textContent = `Orb ${orb.toFixed(1)}° · ${helioView ? 'Helio' : 'Geo'}`;
  box.appendChild(head);

  const grid = document.createElement('div');
  grid.className = 'tp-grid';
  for (const p of planets) {
    const lon = lonForTooltip(p, j);
    if (lon == null) continue;
    const sym = document.createElement('span');
    sym.className = 'tp-sym';
    sym.textContent = planetSym(p);
    const line = document.createElement('span');
    line.className = 'tp-line';
    line.textContent = `${formatLon(lon)} · ${lon.toFixed(1)}°`;
    grid.appendChild(sym);
    grid.appendChild(line);
  }
  box.appendChild(grid);

  if (aspects.length) {
    const asp = document.createElement('div');
    asp.className = 'tp-aspects';
    const nameMap = { conj: '0°', sext: '60°', sq: '90°', tri: '120°', opp: '180°' };
    for (const a of aspects) {
      const row = document.createElement('div');
      row.className = 'tp-aspect-row';
      row.textContent =
        `${planetSym(a.a)}${planetSym(a.b)} ${nameMap[a.aspect] ?? a.aspect} · sep ${a.sep.toFixed(1)}° · ±${a.orb.toFixed(1)}°`;
      asp.appendChild(row);
    }
    box.appendChild(asp);
  }
}

/** Re-apply geo vs helio to the open tooltip using the last ephemeris response. */
export function refreshTooltipPlanetDisplay() {
  if (!lastEphemJson || !planetBox || !state.planets.selected.length) return;
  if (tooltip.style.display === 'none') return;
  const planets = selectedPlanets();
  renderPlanetBoxData(planetBox, lastEphemJson, planets, orbDeg());
}

export function setupTooltip() {
  chart.subscribeCrosshairMove(param => {
    if (!param.point) { tooltip.style.display = 'none'; return; }
    const c = param.seriesData?.get(candleSeries);
    if (!c) { tooltip.style.display = 'none'; return; }
    tDate.textContent = fmtDateEST(param.time || c.time);
    tO.textContent = fmt(c.open);
    tH.textContent = fmt(c.high);
    tL.textContent = fmt(c.low);
    tC.textContent = fmt(c.close);
    tooltip.style.display = 'block';

    const box = ensurePlanetBox();
    if (!state.planets.enabled || !state.planets.selected.length) {
      box.textContent = '';
      box.className = '';
    } else {
      const ts = Number(param.time || c.time);
      if (Number.isFinite(ts) && ts > 0 && ts !== lastTs) {
        lastTs = ts;
        const reqId = ++lastReqId;
        const planets = selectedPlanets();
        const orb = orbDeg();
        const url = `/api/ephem?ts=${ts}&planets=${encodeURIComponent(planets.join(','))}&orb=${encodeURIComponent(String(orb))}`;
        renderPlanetBoxLoading(box, orb);
        fetch(url).then(r => r.json()).then(j => {
          if (reqId !== lastReqId) return;
          if (!j || j.error) {
            lastEphemJson = null;
            box.textContent = '';
            return;
          }
          lastEphemJson = j;
          renderPlanetBoxData(box, j, planets, orb);
        }).catch(() => {
          if (reqId !== lastReqId) return;
          lastEphemJson = null;
          box.textContent = '';
        });
      }
    }

    const ww = chartEl.parentElement.clientWidth;
    const wh = chartEl.parentElement.clientHeight;
    const tw = tooltip.offsetWidth, th = tooltip.offsetHeight, PAD = 14;
    let x = param.point.x + PAD, y = param.point.y + PAD;
    if (x + tw > ww - 4) x = param.point.x - tw - PAD;
    if (y + th > wh - 4) y = param.point.y - th - PAD;
    tooltip.style.left = x + 'px';
    tooltip.style.top  = y + 'px';
  });
}
