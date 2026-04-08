import { setStatus } from './ui.js';

const DEBOUNCE_MS = 280;
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

export async function resolveBareTicker() {
  const input = $('ticker-input');
  if (!input) return null;
  const raw = input.value.trim();
  if (!raw) return null;
  if (raw.includes(':')) return raw.toUpperCase();
  const res = await fetch(
    `/api/symbol-search?q=${encodeURIComponent(raw)}&limit=1`
  );
  const json = await res.json().catch(() => ({}));
  if (!res.ok || json.error) {
    setStatus(json.error || 'Symbol search failed', 'err');
    return null;
  }
  if (!json.results?.length) {
    setStatus('No match — try EXCHANGE:SYMBOL', 'err');
    return null;
  }
  const full = json.results[0].fullSymbol;
  input.value = full;
  hideSuggest();
  setStatus(`Using ${full}`, '');
  return full;
}

async function runSuggest(query) {
  const box = $('ticker-suggest');
  if (!box) return;
  if (!query || query.includes(':')) {
    hideSuggest();
    return;
  }
  const res = await fetch(
    `/api/symbol-search?q=${encodeURIComponent(query)}&limit=12`
  );
  const json = await res.json().catch(() => ({}));
  if (!res.ok || json.error) {
    box.innerHTML = `<div class="ticker-suggest-empty">${json.error || 'Search failed'}</div>`;
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
    btn.addEventListener('mousedown', e => {
      e.preventDefault();
      $('ticker-input').value = row.fullSymbol;
      hideSuggest();
    });
    frag.appendChild(btn);
  }
  box.appendChild(frag);
  box.classList.add('open');
}

export function initTickerSearch() {
  const input = $('ticker-input');
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

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') hideSuggest();
  });
}
