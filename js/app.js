import { config, shortTickerFromTv } from './config.js';
import { state } from './state.js';
import { initTheme, toggleTheme } from './theme.js';
import { loadBars } from './data/loadBars.js';
import { getTvProxyBaseUrl } from './data/tvClient.js';
import { cacheKey, readCache } from './data/cache.js';
import {
  loadChartLibrary,
  initChartAfterLibLoaded,
  applyChartTheme,
  applyPriceAxisVisibility,
} from './chart/bootstrap.js';
import { draw } from './chart/draw.js';
import { onCrosshair } from './chart/crosshair.js';
import { applySessionBands } from './chart/sessionBands.js';
import { initTickerSearch, resolveBareSymbolIfNeeded } from './tickerSearch.js';

function status(msg) {
  const el = document.getElementById('status');
  if (el) el.textContent = msg;
}

function applyBars(bars, msg) {
  state.allBars = bars;
  state.candleSeries.setData(state.allBars);
  const barTf = document.getElementById('barTf')?.value || '15m';
  applySessionBands(state, state.allBars, barTf);
  draw();
  state.chart.timeScale().fitContent();
  status(msg);
}

async function runLoadData() {
  let symbol = (document.getElementById('symbol')?.value || config.symbol).trim();
  if (symbol && !symbol.includes(':')) {
    status('Resolving symbol…');
    const full = await resolveBareSymbolIfNeeded(symbol);
    if (!full) {
      status('No match — type EXCHANGE:SYMBOL or pick from suggestions.');
      return;
    }
    symbol = full;
    const symIn = document.getElementById('symbol');
    if (symIn) symIn.value = full;
    setHeaderSymbolLabel();
  }
  const barTf = document.getElementById('barTf')?.value || config.defaultBarTf;
  const key = cacheKey(symbol, barTf);
  const cached = readCache(key);
  const hadCache = !!(cached && cached.bars && cached.bars.length);

  if (hadCache) {
    applyBars(cached.bars, `${cached.bars.length} bars (cached) · refreshing…`);
  } else {
    status('Loading…');
  }

  try {
    const { bars } = await loadBars({
      symbol,
      barTf,
      onStatus: status,
    });
    applyBars(
      bars,
      `${bars.length} bars (TV)${hadCache ? ' · updated' : ''}`
    );
  } catch (e) {
    if (!hadCache) {
      status(
        `Error: ${e.message} Save cookies under “TradingView cookie” if you have not yet.`
      );
    } else {
      status(`${cached.bars.length} bars (cached · refresh failed)`);
    }
  }
}

function syncUiChrome() {
  const showLevels = document.getElementById('showLevels')?.checked !== false;
  const info = document.getElementById('info');
  if (info) info.style.display = showLevels ? '' : 'none';
  const showAxis = document.getElementById('showPriceAxis')?.checked !== false;
  applyPriceAxisVisibility(showAxis);
}

function wireControls() {
  document.getElementById('pivTf')?.addEventListener('change', draw);
  document.getElementById('barTf')?.addEventListener('change', () => runLoadData());
  document.getElementById('symbol')?.addEventListener('change', () => runLoadData());
  ['showQ', 'showP', 'showNodes', 'showR2', 'showSessionBands'].forEach((id) => {
    document.getElementById(id)?.addEventListener('change', draw);
  });
  document.getElementById('showLevels')?.addEventListener('change', syncUiChrome);
  document.getElementById('showPriceAxis')?.addEventListener('change', syncUiChrome);
  document.getElementById('theme-toggle')?.addEventListener('click', () => {
    toggleTheme();
    applyChartTheme();
    syncUiChrome();
  });
}

function wireTvPanel() {
  const urlIn = document.getElementById('tvProxyUrl');
  const saved = localStorage.getItem(config.tvProxyUrlStorageKey);
  if (urlIn && saved) urlIn.value = saved;
  urlIn?.addEventListener('change', () => {
    const v = urlIn.value.trim();
    if (v) localStorage.setItem(config.tvProxyUrlStorageKey, v);
    else localStorage.removeItem(config.tvProxyUrlStorageKey);
  });

  const btn = document.getElementById('tvCookieSave');
  const ta = document.getElementById('tvCookie');
  const st = document.getElementById('tvCookieStatus');
  btn?.addEventListener('click', async () => {
    const cookies = ta?.value?.trim();
    if (!cookies) {
      if (st) st.textContent = 'Paste cookie string first.';
      return;
    }
    const base = getTvProxyBaseUrl();
    if (st) st.textContent = 'Saving…';
    try {
      const r = await fetch(`${base}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ cookies }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
      if (st) st.textContent = 'Saved. Reload bars (change symbol or Bar TF).';
    } catch (e) {
      if (st) st.textContent = `Failed: ${e.message}`;
    }
  });
}

function setHeaderSymbolLabel() {
  const sym = (document.getElementById('symbol')?.value || config.symbol).trim();
  const shortSym = shortTickerFromTv(sym);
  const pl = document.getElementById('price-label');
  if (pl && !pl.dataset.userEditing) pl.textContent = `${shortSym} —`;
}

function boot() {
  initTheme();
  const sel = document.getElementById('pivTf');
  if (sel) sel.value = config.defaultPivotMode;
  const barSel = document.getElementById('barTf');
  if (barSel) barSel.value = config.defaultBarTf;
  const symIn = document.getElementById('symbol');
  if (symIn) symIn.value = config.symbol;

  wireControls();
  wireTvPanel();
  initTickerSearch();
  symIn?.addEventListener('input', setHeaderSymbolLabel);
  setHeaderSymbolLabel();

  loadChartLibrary(0, () => {
    initChartAfterLibLoaded(onCrosshair);
    applyChartTheme();
    syncUiChrome();
    runLoadData();
  });
}

boot();
