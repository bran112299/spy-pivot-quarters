/**
 * TradingView symbol suggest (astro / tv-dashboard pattern).
 * Uses the same API base as bars (getTvProxyBaseUrl) so search works when the
 * HTML is served from another port (e.g. http.server) while the Flask API is on 8787.
 */

import { getTvProxyBaseUrl } from './data/tvClient.js';

const DEBOUNCE_MS = 280;

function apiUrl(pathWithQuery) {
  const base = getTvProxyBaseUrl();
  const path = pathWithQuery.startsWith('/') ? pathWithQuery : `/${pathWithQuery}`;
  return `${base}${path}`;
}
let debounceTimer = null;

function $(id) {
  return document.getElementById(id);
}

function hideSuggest() {
  const box = $('ticker-suggest');
  if (!box) return;
  box.classList.remove('open');
  box.innerHTML = '';
}

function showSuggestLoading() {
  const box = $('ticker-suggest');
  if (!box) return;
  box.innerHTML = '<div class="ticker-suggest-empty">Searching…</div>';
  box.classList.add('open');
}

/**
 * Bare ticker (e.g. SPY) → full TV symbol via search. Already-qualified returns as-is.
 * @param {AbortSignal} [signal]
 * @returns {Promise<string|null>} null if no match / error
 */
export async function resolveBareSymbolIfNeeded(raw, signal) {
  const q = (raw || '').trim();
  if (!q) return null;
  if (q.includes(':')) return q.toUpperCase();
  const res = await fetch(
    apiUrl(`/api/symbol-search?q=${encodeURIComponent(q)}&limit=1`),
    { cache: 'no-store', signal }
  );
  const json = await res.json().catch(() => ({}));
  if (!res.ok || json.error) return null;
  if (!json.results?.length) return null;
  return json.results[0].fullSymbol;
}

async function runSuggest(query) {
  const box = $('ticker-suggest');
  if (!box) return;
  if (!query || query.includes(':')) {
    hideSuggest();
    return;
  }
  let res;
  try {
    res = await fetch(
      apiUrl(`/api/symbol-search?q=${encodeURIComponent(query)}&limit=12`),
      { cache: 'no-store' }
    );
  } catch (e) {
    box.innerHTML = `<div class="ticker-suggest-empty">Network: ${e.message}</div>`;
    box.classList.add('open');
    return;
  }
  const text = await res.text();
  let json = {};
  try {
    json = text ? JSON.parse(text) : {};
  } catch {
    box.innerHTML = `<div class="ticker-suggest-empty">Bad response (${res.status}) — use python3 server/app.py and set Proxy URL to your API host if needed.</div>`;
    box.classList.add('open');
    return;
  }
  if (!res.ok || json.error) {
    const detail = json.error || `HTTP ${res.status}`;
    box.innerHTML = `<div class="ticker-suggest-empty">${detail}</div>`;
    box.classList.add('open');
    return;
  }
  const list = json.results || [];
  if (!list.length) {
    box.innerHTML = '<div class="ticker-suggest-empty">No matches</div>';
    box.classList.add('open');
    return;
  }
  box.innerHTML = '';
  const frag = document.createDocumentFragment();
  const input = $('symbol');
  for (const row of list) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'ticker-suggest-row';
    const main = document.createElement('div');
    main.className = 'ticker-suggest-sym';
    main.textContent = row.fullSymbol;
    const sub = document.createElement('div');
    sub.className = 'ticker-suggest-desc';
    sub.textContent = row.description || row.type || '';
    btn.appendChild(main);
    btn.appendChild(sub);
    btn.addEventListener('mousedown', (e) => {
      e.preventDefault();
      if (input) {
        input.value = row.fullSymbol;
        hideSuggest();
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    });
    frag.appendChild(btn);
  }
  box.appendChild(frag);
  box.classList.add('open');
}

/**
 * @param {{ onStatus?: (msg: string) => void }} [deps]
 */
export function initTickerSearch() {
  const input = $('symbol');
  const box = $('ticker-suggest');
  if (!input || !box) return;

  input.addEventListener('input', () => {
    if (debounceTimer) clearTimeout(debounceTimer);
    const q = input.value.trim();
    if (!q || q.includes(':')) {
      hideSuggest();
      return;
    }
    showSuggestLoading();
    debounceTimer = setTimeout(() => {
      debounceTimer = null;
      runSuggest(q);
    }, DEBOUNCE_MS);
  });

  input.addEventListener('focus', () => {
    const q = input.value.trim();
    if (q && !q.includes(':')) runSuggest(q);
  });

  input.addEventListener('blur', () => {
    setTimeout(hideSuggest, 150);
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') hideSuggest();
  });
}
