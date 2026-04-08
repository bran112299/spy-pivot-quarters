import { state } from './state.js';
import { applyCrosshairForMeasure } from './chart.js';
import { renderAllMeasurements, clearAllMeasurements } from './measure.js';
import { invalidateEphemTooltipCache, refreshTooltipPlanetDisplay } from './tooltip.js';

function $(id) { return document.getElementById(id); }

export function getSelectedPlanets() {
  return [...state.planets.selected];
}

export function getOrbDeg() {
  const v = Number(state.planets.orbDeg);
  return Number.isFinite(v) ? Math.max(0, Math.min(10, v)) : 1.0;
}

export function syncPlanetUIFromState() {
  const wrap = $('planet-wrap');
  const orbEl = $('orb-input');
  if (orbEl) orbEl.value = String(getOrbDeg());

  if (wrap) {
    wrap.querySelectorAll('input[type="checkbox"][data-planet]').forEach(cb => {
      cb.checked = state.planets.selected.includes(cb.dataset.planet);
    });
  }
  $('measure-toggle')?.classList.toggle('active', !!state.measure.on);
  const helioCb = $('measure-helio');
  if (helioCb) helioCb.checked = !!state.planets.helio;
}

export function toggleHelioDisplay() {
  state.planets.helio = !state.planets.helio;
  const helioCb = $('measure-helio');
  if (helioCb) helioCb.checked = state.planets.helio;
  refreshTooltipPlanetDisplay();
  renderAllMeasurements();
}

export function initPlanetUI() {
  $('measure-helio')?.addEventListener('change', e => {
    state.planets.helio = !!e.target.checked;
    refreshTooltipPlanetDisplay();
    renderAllMeasurements();
  });

  document.addEventListener('keydown', e => {
    if (e.defaultPrevented) return;
    const el = e.target;
    if (el && typeof el.closest === 'function' && el.closest('input, textarea, select, [contenteditable="true"]')) {
      return;
    }
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === 'm' || e.key === 'M') {
      e.preventDefault();
      toggleMeasure();
      return;
    }
    if (e.key === 'h' || e.key === 'H') {
      e.preventDefault();
      toggleHelioDisplay();
    }
  });

  const panel = $('planet-panel');
  const wrap  = $('planet-wrap');
  if (panel && wrap) {
    document.addEventListener('click', e => {
      if (!panel.classList.contains('open')) return;
      if (wrap.contains(e.target)) return;
      panel.classList.remove('open');
      $('planet-btn')?.classList.remove('active');
    });

    wrap.querySelectorAll('input[type="checkbox"][data-planet]').forEach(cb => {
      cb.addEventListener('change', () => {
        const p = cb.dataset.planet;
        if (!p) return;
        if (cb.checked) {
          if (!state.planets.selected.includes(p)) state.planets.selected.push(p);
        } else {
          state.planets.selected = state.planets.selected.filter(x => x !== p);
        }
        invalidateEphemTooltipCache();
      });
    });
  }

  $('orb-input')?.addEventListener('input', e => {
    const val = Number(e.target.value);
    if (Number.isFinite(val)) state.planets.orbDeg = Math.max(0, Math.min(10, val));
    invalidateEphemTooltipCache();
  });

  syncPlanetUIFromState();
}

export function togglePlanetPanel() {
  const panel = $('planet-panel');
  const btn   = $('planet-btn');
  if (!panel || !btn) return;
  const open = !panel.classList.contains('open');
  panel.classList.toggle('open', open);
  btn.classList.toggle('active', open);
}

export function toggleMeasure() {
  state.measure.on = !state.measure.on;
  state.measure.draftTs0 = null;
  $('measure-toggle')?.classList.toggle('active', !!state.measure.on);
  applyCrosshairForMeasure(!!state.measure.on);
  const hint = $('measure-hint');
  if (hint) {
    hint.textContent = state.measure.on ? 'Click start candle on chart…' : '';
  }
  renderAllMeasurements();
}

/** Exposed for onclick in HTML */
export function clearAllMeasures() {
  clearAllMeasurements();
}

